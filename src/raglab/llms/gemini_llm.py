"""Google Gemini chat adapter (requires ``providers`` extra + GOOGLE_API_KEY).

Uses the current ``google-genai`` SDK.
"""

from __future__ import annotations

import os
from typing import Any

from raglab.core.registry import register
from raglab.core.types import LLMResponse
from raglab.errors import (
    MissingDependencyError,
    ModelNotFoundError,
    ProviderAuthError,
    call_with_retries,
)
from raglab.llms.costs import cost_usd


@register("llm", "gemini")
class GeminiLLM:
    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
        **_: object,
    ) -> None:
        self._model = model or "gemini-2.5-flash"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client: Any = None

    def _ensure(self):
        if self._client is None:
            try:
                from google import genai
            except ImportError as e:
                raise MissingDependencyError(
                    "Gemini needs the 'providers' extra: pip install 'raglab[providers]'"
                ) from e
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise ProviderAuthError(
                    "gemini: environment variable GOOGLE_API_KEY is not set."
                )
            self._client = genai.Client(api_key=api_key)
        return self._client

    def _fatal(self, exc: Exception):
        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        if code == 404 or "not found" in str(exc).lower():
            return ModelNotFoundError(
                f"gemini: model {self._model!r} not found or unavailable."
            )
        if code in (401, 403):
            return ProviderAuthError("gemini: authentication failed — check GOOGLE_API_KEY.")
        return None

    @staticmethod
    def _transient(exc: Exception) -> bool:
        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        return (code is not None and code >= 500) or code == 429

    @property
    def model(self) -> str:
        return self._model

    def generate(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        client = self._ensure()
        from google.genai import types

        system = "\n".join(m["content"] for m in messages if m.get("role") == "system")
        user = "\n".join(m["content"] for m in messages if m.get("role") != "system")
        config = types.GenerateContentConfig(
            system_instruction=system or None,
            temperature=float(kwargs.get("temperature", self.temperature)),
            max_output_tokens=int(kwargs.get("max_tokens", self.max_tokens)),
        )

        resp = call_with_retries(
            lambda: client.models.generate_content(
                model=self._model, contents=user, config=config
            ),
            is_fatal=self._fatal,
            is_transient=self._transient,
            max_retries=int(kwargs.get("max_retries", 4)),
            label=f"gemini:{self._model}",
        )
        text = resp.text or ""
        usage = getattr(resp, "usage_metadata", None)
        pt = getattr(usage, "prompt_token_count", 0) or 0
        ct = getattr(usage, "candidates_token_count", 0) or 0
        return LLMResponse(
            text=text,
            model=self._model,
            prompt_tokens=pt,
            completion_tokens=ct,
            usd_cost=cost_usd(self._model, pt, ct),
        )
