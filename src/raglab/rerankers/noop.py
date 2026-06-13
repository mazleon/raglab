"""Identity reranker — preserves retrieval order, just truncates to top_n.

The offline default so the hybrid/agentic pipelines run with no model or key.
"""

from __future__ import annotations

from raglab.core.registry import register
from raglab.core.types import ScoredChunk


@register("reranker", "noop")
class NoopReranker:
    def __init__(self, model: str | None = None, **_: object) -> None:
        pass

    def rerank(
        self, query: str, chunks: list[ScoredChunk], top_n: int
    ) -> list[ScoredChunk]:
        return chunks[:top_n]
