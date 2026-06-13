"""Offline extractive 'LLM'.

Produces deterministic answers by selecting the sentences from the provided
context that overlap most with the question. It is not a language model — it
exists so every pipeline (including the agentic loop, grader, and critic) runs
end-to-end with zero API keys, and so benchmark proxy metrics are meaningful.

Swap ``llm.provider`` to ``openai`` or ``openrouter`` for real generation.
"""

from __future__ import annotations

import re

from raglab.core.registry import register
from raglab.core.types import LLMResponse

_SENT = re.compile(r"(?<=[.!?])\s+")
_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = {
    "the", "a", "an", "is", "are", "of", "to", "and", "in", "on", "for", "what",
    "does", "do", "how", "why", "which", "that", "this", "with", "as", "by", "it",
}


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN.findall(text.lower()) if t not in _STOP}


def _extract_question(content: str) -> str:
    for line in reversed(content.splitlines()):
        low = line.strip().lower()
        if low.startswith("question:"):
            return line.split(":", 1)[1].strip()
    # Fallback: last non-empty line.
    lines = [ln for ln in content.splitlines() if ln.strip()]
    return lines[-1] if lines else content


def _extract_context(content: str) -> str:
    # Everything before a trailing "Question:" line is treated as context.
    parts = re.split(r"\n\s*Question:", content, maxsplit=1)
    return parts[0]


@register("llm", "echo")
class EchoLLM:
    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
        **_: object,
    ) -> None:
        self._model = model or "echo-extractive"
        self.max_tokens = max_tokens

    @property
    def model(self) -> str:
        return self._model

    def generate(self, messages: list[dict[str, str]], **_: object) -> LLMResponse:
        content = "\n".join(m.get("content", "") for m in messages)
        question = _extract_question(content)
        context = _extract_context(content)
        q_tokens = _tokens(question)

        sentences = [s.strip() for s in _SENT.split(context) if len(s.strip()) > 15]
        scored = sorted(
            sentences,
            key=lambda s: len(q_tokens & _tokens(s)),
            reverse=True,
        )
        top = [s for s in scored[:2] if q_tokens & _tokens(s)]
        answer = " ".join(top) if top else (scored[0] if scored else "I don't know.")

        prompt_tokens = len(content.split())
        completion_tokens = len(answer.split())
        return LLMResponse(
            text=answer,
            model=self._model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            usd_cost=0.0,
        )
