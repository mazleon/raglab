"""Tests for the error hierarchy, retry helper, and judge metering."""

import pytest

from raglab.core.config import config_from_dict
from raglab.core.types import LLMResponse
from raglab.errors import (
    ConfigError,
    ModelNotFoundError,
    ProviderError,
    ProviderRateLimitError,
    call_with_retries,
)
from raglab.llms.metered import MeteredLLM


class _Boom(Exception):
    def __init__(self, status):
        super().__init__(f"status {status}")
        self.status_code = status


def test_invalid_embedding_raises_config_error():
    with pytest.raises(ConfigError):
        config_from_dict({"embedding": {"name": "openrouter"}})


def test_retries_fatal_fails_fast():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise _Boom(404)

    def fatal(e):
        return ModelNotFoundError("nope") if getattr(e, "status_code", None) == 404 else None

    with pytest.raises(ModelNotFoundError):
        call_with_retries(fn, is_fatal=fatal, is_transient=lambda e: False, max_retries=4)
    assert calls["n"] == 1  # no retries on a fatal error


def test_retries_transient_then_exhausts():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise _Boom(503)

    with pytest.raises(ProviderRateLimitError):
        call_with_retries(
            fn,
            is_fatal=lambda e: None,
            is_transient=lambda e: True,
            max_retries=3,
            base_delay=0.0,
        )
    assert calls["n"] == 3


def test_retries_non_transient_wrapped_as_provider_error():
    with pytest.raises(ProviderError):
        call_with_retries(
            lambda: (_ for _ in ()).throw(_Boom(400)),
            is_fatal=lambda e: None,
            is_transient=lambda e: False,
        )


def test_retries_success_returns_value():
    assert call_with_retries(
        lambda: 42, is_fatal=lambda e: None, is_transient=lambda e: False
    ) == 42


class _FakeLLM:
    model = "fake"

    def generate(self, messages, **kw):
        return LLMResponse(
            text="0.5", model="fake", prompt_tokens=10, completion_tokens=5, usd_cost=0.01
        )


def test_metered_llm_accumulates():
    m = MeteredLLM(_FakeLLM())
    m.generate([{"role": "user", "content": "hi"}])
    m.generate([{"role": "user", "content": "hi"}])
    assert m.calls == 2
    assert abs(m.total_cost - 0.02) < 1e-9
    assert m.total_tokens == 30
