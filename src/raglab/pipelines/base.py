"""Shared pipeline plumbing: prompt formatting and grounded generation.

The prompt format (numbered context block followed by a ``Question:`` line) is
shared by every architecture and is also what the offline EchoLLM parses, so
pipelines behave consistently across real and offline models.
"""

from __future__ import annotations

from raglab.core.config import Components
from raglab.core.types import LLMResponse, RunMetrics, ScoredChunk

SYSTEM_PROMPT = (
    "You are a precise assistant. Answer the question using ONLY the provided "
    "context. Cite supporting sources inline as [n]. If the context is "
    "insufficient, say you don't know."
)


def format_context(contexts: list[ScoredChunk]) -> str:
    lines = []
    for i, sc in enumerate(contexts, start=1):
        src = sc.chunk.metadata.get("source", sc.chunk.document_id)
        lines.append(f"[{i}] (source: {src})\n{sc.chunk.text}")
    return "\n\n".join(lines)


def build_messages(query: str, contexts: list[ScoredChunk]) -> list[dict[str, str]]:
    user = f"Context:\n{format_context(contexts)}\n\nQuestion: {query}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


class BasePipeline:
    """Holds resolved components and a metrics accumulator helper."""

    name: str = "base"

    def __init__(self, components: Components) -> None:
        self.c = components

    def _generate(
        self, query: str, contexts: list[ScoredChunk], metrics: RunMetrics
    ) -> LLMResponse:
        resp = self.c.llm.generate(build_messages(query, contexts))
        metrics.add_llm(resp)
        return resp
