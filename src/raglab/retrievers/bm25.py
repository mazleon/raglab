"""Sparse BM25 keyword retriever over all chunks in the store.

Builds an in-memory BM25 index from ``store.all_chunks()`` lazily on first use.
For M1 corpora this is fine; large corpora would move to a server-side sparse
index (a future phase).
"""

from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

from raglab.core.interfaces import VectorStore
from raglab.core.registry import register
from raglab.core.types import Chunk, ScoredChunk

_TOKEN = re.compile(r"[a-z0-9]+")


def _tok(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


@register("retriever", "bm25")
class BM25Retriever:
    def __init__(self, store: VectorStore, **_: object) -> None:
        self.store = store
        self._chunks: list[Chunk] = []
        self._bm25: BM25Okapi | None = None

    def _ensure_index(self) -> None:
        if self._bm25 is None:
            self._chunks = self.store.all_chunks()
            corpus = [_tok(c.text) for c in self._chunks] or [[""]]
            self._bm25 = BM25Okapi(corpus)

    def retrieve(self, query: str, k: int) -> list[ScoredChunk]:
        self._ensure_index()
        if not self._chunks:
            return []
        scores = self._bm25.get_scores(_tok(query))  # type: ignore[union-attr]
        ranked = sorted(
            zip(self._chunks, scores, strict=True), key=lambda x: x[1], reverse=True
        )
        return [ScoredChunk(c, float(s)) for c, s in ranked[:k]]
