"""OpenAI and OpenRouter chat adapters.

Both speak the OpenAI Chat Completions API, so they share one implementation;
OpenRouter just points at a different base_url and key. Token usage from the
response drives cost via the price table.
"""

from __future__ import annotations

import os
from typing import Any

from raglab.core.registry import register
from raglab.core.types import LLMResponse
from raglab.llms.costs import cost_usd


class _OpenAICompatLLM:
    _default_model = ""
    _base_url: str | None = None
    _api_key_env = "OPENAI_API_KEY"

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
        **_: object,
    ) -> None:
        self._model = model or self._default_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client: Any = None

    def _ensure(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as e:  # pragma: no cover
                raise ImportError(
                    "OpenAI/OpenRouter need the 'providers' extra: "
                    "pip install 'raglab[providers]'"
                ) from e
            base_url = self._base_url or os.environ.get("OPENROUTER_BASE_URL")
            self._client = OpenAI(
                api_key=os.environ.get(self._api_key_env),
                base_url=base_url if self._base_url else None,
            )
        return self._client

    @property
    def model(self) -> str:
        return self._model

    def generate(self, messages: list[dict[str, str]], **kwargs: object) -> LLMResponse:
        client = self._ensure()
        resp = client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
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


@register("llm", "openai")
class OpenAILLM(_OpenAICompatLLM):
    _default_model = "gpt-4o-mini"
    _api_key_env = "OPENAI_API_KEY"


@register("llm", "openrouter")
class OpenRouterLLM(_OpenAICompatLLM):
    _default_model = "google/gemma-4-31b:free"
    _base_url = "https://openrouter.ai/api/v1"
    _api_key_env = "OPENROUTER_API_KEY"
