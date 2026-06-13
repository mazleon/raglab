"""Multi-query retriever: paraphrase the query into N variants, retrieve each,
and fuse with RRF. Variant generation is pluggable; the default produces simple
deterministic lexical variants so it works offline (an LLM can be wired in)."""

from __future__ import annotations

from raglab.core.interfaces import Retriever
from raglab.core.registry import register
from raglab.core.types import ScoredChunk
from raglab.retrievers.fusion import reciprocal_rank_fusion


def _variants(query: str, n: int) -> list[str]:
    base = query.strip().rstrip("?.")
    variants = [
        query,
        f"What is {base}?",
        f"Explain {base}.",
        f"Tell me about {base}.",
    ]
    return variants[:n] if n <= len(variants) else variants


@register("retriever", "multi_query")
class MultiQueryRetriever:
    def __init__(self, base: Retriever, n_queries: int = 3, **_: object) -> None:
        self.base = base
        self.n_queries = n_queries

    def retrieve(self, query: str, k: int) -> list[ScoredChunk]:
        lists = [self.base.retrieve(q, k) for q in _variants(query, self.n_queries)]
        return reciprocal_rank_fusion(lists)[:k]
