"""Hybrid RAG: (dense + BM25) fused retrieval -> rerank -> generate."""

from __future__ import annotations

from raglab.core.registry import register
from raglab.core.types import RAGResult, RunMetrics, TrajectoryStep, timer
from raglab.pipelines.base import BasePipeline


@register("architecture", "hybrid_rag")
class HybridRAG(BasePipeline):
    name = "hybrid_rag"

    def run(self, query: str) -> RAGResult:
        metrics = RunMetrics()
        traj: list[TrajectoryStep] = []
        cfg = self.c.config
        with timer(metrics):
            candidates = self.c.retriever.retrieve(query, cfg.retrieval.k)
            traj.append(TrajectoryStep("hybrid_retrieve", f"{len(candidates)} candidates"))

            contexts = self.c.reranker.rerank(query, candidates, cfg.reranker.top_n)
            metrics.retriever_hits = len(contexts)
            traj.append(TrajectoryStep("rerank", f"top {len(contexts)}"))

            resp = self._generate(query, contexts, metrics)
            traj.append(TrajectoryStep("generate", resp.model))

        return RAGResult(
            query=query,
            answer=resp.text,
            contexts=contexts,
            trajectory=traj,
            metrics=metrics,
            architecture=self.name,
        )
