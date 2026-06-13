"""Hybrid retriever: dense + BM25, fused with RRF or MMR."""

from __future__ import annotations

from raglab.core.interfaces import Embedder, Retriever
from raglab.core.registry import register
from raglab.core.types import ScoredChunk
from raglab.retrievers.fusion import mmr, reciprocal_rank_fusion


@register("retriever", "hybrid")
class HybridRetriever:
    def __init__(
        self,
        dense: Retriever,
        bm25: Retriever,
        dense_k: int = 20,
        bm25_k: int = 20,
        fusion: str = "rrf",
        rrf_k: int = 60,
        mmr_lambda: float = 0.5,
        embedder: Embedder | None = None,
        **_: object,
    ) -> None:
        self.dense = dense
        self.bm25 = bm25
        self.dense_k = dense_k
        self.bm25_k = bm25_k
        self.fusion = fusion
        self.rrf_k = rrf_k
        self.mmr_lambda = mmr_lambda
        self.embedder = embedder

    def retrieve(self, query: str, k: int) -> list[ScoredChunk]:
        dense_hits = self.dense.retrieve(query, self.dense_k)
        bm25_hits = self.bm25.retrieve(query, self.bm25_k)

        if self.fusion == "mmr":
            if self.embedder is None:
                raise ValueError("MMR fusion requires an embedder")
            # Deduplicate union of candidates.
            seen: dict[str, ScoredChunk] = {}
            for sc in dense_hits + bm25_hits:
                seen.setdefault(sc.chunk.chunk_id or sc.chunk.text, sc)
            candidates = list(seen.values())
            qv = self.embedder.embed_query(query)
            cvs = self.embedder.embed_documents([c.text for c in candidates])
            return mmr(qv, candidates, cvs, k, self.mmr_lambda)

        fused = reciprocal_rank_fusion([dense_hits, bm25_hits], self.rrf_k)
        return fused[:k]
