"""Cohere Rerank adapter (requires the ``providers`` extra + COHERE_API_KEY)."""

from __future__ import annotations

import os
from typing import Any

from raglab.core.registry import register
from raglab.core.types import ScoredChunk
from raglab.errors import (
    MissingDependencyError,
    ModelNotFoundError,
    ProviderAuthError,
    call_with_retries,
)


def _status(exc: Exception) -> int | None:
    return getattr(exc, "status_code", None)


@register("reranker", "cohere")
class CohereReranker:
    def __init__(self, model: str | None = None, **_: object) -> None:
        self._model = model or "rerank-v4.0-fast"
        self._client: Any = None

    def _ensure(self):
        if self._client is None:
            try:
                import cohere
            except ImportError as e:
                raise MissingDependencyError(
                    "Cohere rerank needs the 'providers' extra: pip install 'raglab[providers]'"
                ) from e
            api_key = os.environ.get("COHERE_API_KEY")
            if not api_key:
                raise ProviderAuthError(
                    "cohere: environment variable COHERE_API_KEY is not set."
                )
            self._client = cohere.Client(api_key)
        return self._client

    def _fatal(self, exc: Exception):
        status = _status(exc)
        if status == 404:
            return ModelNotFoundError(f"cohere: rerank model {self._model!r} not found.")
        if status in (401, 403):
            return ProviderAuthError("cohere: authentication failed — check COHERE_API_KEY.")
        return None

    @staticmethod
    def _transient(exc: Exception) -> bool:
        status = _status(exc)
        return status == 429 or (status is not None and status >= 500)

    def rerank(
        self, query: str, chunks: list[ScoredChunk], top_n: int
    ) -> list[ScoredChunk]:
        if not chunks:
            return []
        client = self._ensure()
        resp = call_with_retries(
            lambda: client.rerank(
                model=self._model,
                query=query,
                documents=[c.text for c in chunks],
                top_n=min(top_n, len(chunks)),
            ),
            is_fatal=self._fatal,
            is_transient=self._transient,
            label=f"cohere-rerank:{self._model}",
        )
        return [
            ScoredChunk(chunks[r.index].chunk, float(r.relevance_score))
            for r in resp.results
        ]
