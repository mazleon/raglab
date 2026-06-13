"""Naive RAG: retrieve -> generate. The baseline."""

from __future__ import annotations

from raglab.core.registry import register
from raglab.core.types import RAGResult, RunMetrics, TrajectoryStep, timer
from raglab.pipelines.base import BasePipeline


@register("architecture", "naive_rag")
class NaiveRAG(BasePipeline):
    name = "naive_rag"

    def run(self, query: str) -> RAGResult:
        metrics = RunMetrics()
        traj: list[TrajectoryStep] = []
        with timer(metrics):
            contexts = self.c.retriever.retrieve(query, self.c.config.retrieval.k)
            metrics.retriever_hits = len(contexts)
            traj.append(TrajectoryStep("retrieve", f"{len(contexts)} chunks"))

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
