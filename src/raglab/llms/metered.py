"""A pass-through LLM wrapper that meters token usage and cost.

Used by the benchmark runner so judge-LLM spend is attributed and reported
separately from the answer-generation LLM.
"""

from __future__ import annotations

from typing import Any

from raglab.core.interfaces import LLM
from raglab.core.types import LLMResponse


class MeteredLLM:
    def __init__(self, inner: LLM) -> None:
        self.inner = inner
        self.total_cost = 0.0
        self.total_tokens = 0
        self.calls = 0

    @property
    def model(self) -> str:
        return self.inner.model

    def generate(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        resp = self.inner.generate(messages, **kwargs)
        self.total_cost += resp.usd_cost
        self.total_tokens += resp.total_tokens
        self.calls += 1
        return resp
