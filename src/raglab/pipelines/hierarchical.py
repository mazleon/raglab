"""Hierarchical RAG: two-level retrieval.

Level 1 selects the most relevant *documents* (via an initial retrieval pass),
Level 2 gathers all chunks within those documents and reranks them. This mirrors
summary-tree / hierarchical retrieval and shines when answers need a document's
broader context rather than isolated snippets.
"""

from __future__ import annotations

from collections import OrderedDict

from raglab.core.registry import register
from raglab.core.types import RAGResult, RunMetrics, ScoredChunk, TrajectoryStep, timer
from raglab.pipelines import helpers
from raglab.pipelines.base import BasePipeline


@register("architecture", "hierarchical_rag")
class HierarchicalRAG(BasePipeline):
    name = "hierarchical_rag"

    def run(self, query: str) -> RAGResult:
        metrics = RunMetrics()
        traj: list[TrajectoryStep] = []
        cfg = self.c.config
        with timer(metrics):
            # Level 1: which documents are relevant?
            seeds = helpers.retrieve(self.c, query, cfg.retrieval.k)
            top_docs: OrderedDict[str, None] = OrderedDict()
            for sc in seeds:
                top_docs.setdefault(sc.chunk.document_id, None)
                if len(top_docs) >= 2:
                    break
            traj.append(TrajectoryStep("select_docs", f"{len(top_docs)} documents"))

            # Level 2: expand within those documents.
            all_chunks = self.c.store.all_chunks()
            pool = [
                ScoredChunk(c, 0.0) for c in all_chunks if c.document_id in top_docs
            ]
            if not pool:
                pool = seeds
            traj.append(TrajectoryStep("expand", f"{len(pool)} chunks in scope"))

            contexts = helpers.rerank(self.c, query, pool, cfg.reranker.top_n)
            metrics.retriever_hits = len(contexts)
            resp = helpers.generate(self.c, query, contexts, metrics)
            traj.append(TrajectoryStep("generate", resp.model))

        return RAGResult(query, resp.text, contexts, traj, metrics, self.name)
