"""Shared base for OpenAI Chat-Completions-compatible LLM adapters.

OpenAI and OpenRouter speak the same API, so both concrete adapters subclass this
one base. Keeping the base here (rather than inside ``openai_llm.py``) means each
provider file imports a named, non-private module — no cross-file reach into
another adapter's internals.

The ``openai`` SDK is imported lazily so the package still imports (and the whole
offline slice still runs) when the ``providers`` extra is not installed.
Transient failures (rate limits, timeouts, 5xx) are retried with backoff;
fatal failures (bad model, bad key) fail fast with a clear RAGLab error.
"""

from __future__ import annotations

import os
from typing import Any

from raglab.core.types import LLMResponse
from raglab.errors import (
    MissingDependencyError,
    ModelNotFoundError,
    ProviderAuthError,
    ProviderResponseError,
    call_with_retries,
)
from raglab.llms.costs import cost_usd


def _status(exc: Exception) -> int | None:
    return getattr(exc, "status_code", None) or getattr(exc, "code", None)


class OpenAICompatLLM:
    """Base for any LLM that talks the OpenAI Chat Completions API.

    Subclasses set the class attributes (``_default_model``, ``_base_url``,
    ``_api_key_env``, ``_provider``) and register themselves; the behaviour is
    identical otherwise.
    """

    _default_model = ""
    _base_url: str | None = None
    _api_key_env = "OPENAI_API_KEY"
    _provider = "openai"

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
        max_retries: int = 4,
        **_: object,
    ) -> None:
        self._model = model or self._default_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self._client: Any = None

    def _ensure(self) -> Any:
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as e:
                raise MissingDependencyError(
                    f"{self._provider} needs the 'providers' extra: "
                    "pip install 'raglab[providers]'"
                ) from e
            api_key = os.environ.get(self._api_key_env)
            if not api_key:
                raise ProviderAuthError(
                    f"{self._provider}: environment variable {self._api_key_env} is not set."
                )
            base_url = self._base_url or os.environ.get("OPENROUTER_BASE_URL")
            self._client = OpenAI(
                api_key=api_key, base_url=base_url if self._base_url else None
            )
        return self._client

    @property
    def model(self) -> str:
        return self._model

    # --- error classification ---
    def _fatal(self, exc: Exception):
        from openai import AuthenticationError, NotFoundError, PermissionDeniedError

        status = _status(exc)
        msg = str(exc).lower()
        # OpenRouter returns 404 for unavailable models and 400 "not a valid
        # model ID" for unknown slugs — both are a model mistake, not transient.
        if (
            isinstance(exc, NotFoundError)
            or status == 404
            or (status == 400 and "model" in msg)
        ):
            return ModelNotFoundError(
                f"{self._provider}: model {self._model!r} not found or unavailable. "
                "Check the model id (free OpenRouter slugs often require the paid slug)."
            )
        if isinstance(exc, AuthenticationError | PermissionDeniedError) or status in (401, 403):
            return ProviderAuthError(
                f"{self._provider}: authentication failed — check {self._api_key_env}."
            )
        return None

    def _transient(self, exc: Exception) -> bool:
        from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError

        status = _status(exc)
        return isinstance(
            exc,
            RateLimitError | APITimeoutError | APIConnectionError | InternalServerError,
        ) or (status is not None and status >= 500)

    def _retry_after(self, exc: Exception) -> float | None:
        resp = getattr(exc, "response", None)
        headers = getattr(resp, "headers", None) or {}
        for key in ("retry-after", "x-ratelimit-reset-requests", "x-ratelimit-reset"):
            val = headers.get(key)
            if val:
                try:
                    return float(val)
                except ValueError:
                    continue
        return None

    def generate(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        client = self._ensure()
        temperature = float(kwargs.get("temperature", self.temperature))
        max_tokens = int(kwargs.get("max_tokens", self.max_tokens))

        def _call():
            return client.chat.completions.create(
                model=self._model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
            )

        resp = call_with_retries(
            _call,
            is_fatal=self._fatal,
            is_transient=self._transient,
            retry_after=self._retry_after,
            max_retries=int(kwargs.get("max_retries", self.max_retries)),
            label=f"{self._provider}:{self._model}",
        )

        if not resp.choices:
            raise ProviderResponseError(
                f"{self._provider}: {self._model!r} returned no choices."
            )
        text = resp.choices[0].message.content or ""
        usage = resp.usage
        pt = getattr(usage, "prompt_tokens", 0) or 0
        ct = getattr(usage, "completion_tokens", 0) or 0
        return LLMResponse(
            text=text,
            model=self._model,
            prompt_tokens=pt,
            completion_tokens=ct,
            usd_cost=cost_usd(self._model, pt, ct),
        )