"""Cohere Rerank adapter (requires the ``providers`` extra + COHERE_API_KEY)."""

from __future__ import annotations

import os

from raglab.core.registry import register
from raglab.core.types import ScoredChunk


@register("reranker", "cohere")
class CohereReranker:
    def __init__(self, model: str | None = None, **_: object) -> None:
        self._model = model or "rerank-english-v3.0"
        self._client = None

    def _ensure(self):
        if self._client is None:
            try:
                import cohere
            except ImportError as e:  # pragma: no cover
                raise ImportError(
                    "Cohere rerank needs the 'providers' extra: pip install 'raglab[providers]'"
                ) from e
            self._client = cohere.Client(os.environ.get("COHERE_API_KEY"))
        return self._client

    def rerank(
        self, query: str, chunks: list[ScoredChunk], top_n: int
    ) -> list[ScoredChunk]:
        if not chunks:
            return []
        client = self._ensure()
        resp = client.rerank(
            model=self._model,
            query=query,
            documents=[c.text for c in chunks],
            top_n=min(top_n, len(chunks)),
        )
        return [
            ScoredChunk(chunks[r.index].chunk, float(r.relevance_score))
            for r in resp.results
        ]
