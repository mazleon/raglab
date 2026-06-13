"""Multi-Hop RAG: decompose the question into sub-questions, retrieve + answer
each hop, accumulate the evidence, then synthesize a final grounded answer."""

from __future__ import annotations

from raglab.agents.reasoning import decompose
from raglab.core.registry import register
from raglab.core.types import RAGResult, RunMetrics, TrajectoryStep, timer
from raglab.pipelines import helpers
from raglab.pipelines.base import BasePipeline


@register("architecture", "multi_hop_rag")
class MultiHopRAG(BasePipeline):
    name = "multi_hop_rag"

    def run(self, query: str) -> RAGResult:
        metrics = RunMetrics()
        traj: list[TrajectoryStep] = []
        cfg = self.c.config
        with timer(metrics):
            subqs = decompose(query, max_subs=3, llm=self.c.llm)
            traj.append(TrajectoryStep("decompose", f"{len(subqs)} hops"))

            evidence = []
            for i, sub in enumerate(subqs, 1):
                hits = helpers.retrieve(self.c, sub, cfg.retrieval.k)
                hits = helpers.rerank(self.c, sub, hits, cfg.reranker.top_n)
                evidence.extend(hits)
                traj.append(TrajectoryStep(f"hop{i}", f"{sub} -> {len(hits)} ctx"))

            contexts = helpers.dedup(evidence)[: cfg.reranker.top_n + 2]
            metrics.retriever_hits = len(contexts)
            resp = helpers.generate(self.c, query, contexts, metrics)
            traj.append(TrajectoryStep("synthesize", resp.model))

        return RAGResult(query, resp.text, contexts, traj, metrics, self.name)
