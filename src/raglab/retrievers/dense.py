"""Dense vector retriever — embeds the query and searches the vector store."""

from __future__ import annotations

from raglab.core.interfaces import Embedder, VectorStore
from raglab.core.registry import register
from raglab.core.types import ScoredChunk


@register("retriever", "dense")
class DenseRetriever:
    def __init__(self, embedder: Embedder, store: VectorStore, **_: object) -> None:
        self.embedder = embedder
        self.store = store

    def retrieve(self, query: str, k: int) -> list[ScoredChunk]:
        vector = self.embedder.embed_query(query)
        return self.store.search(vector, k)
