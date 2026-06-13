"""Advanced RAG: multi-query expansion -> fused retrieval -> parent expansion
-> rerank -> generate. A stronger non-agentic baseline than Hybrid."""

from __future__ import annotations

from raglab.agents.reasoning import decompose
from raglab.core.registry import register
from raglab.core.types import RAGResult, RunMetrics, TrajectoryStep, timer
from raglab.pipelines import helpers
from raglab.pipelines.base import BasePipeline
from raglab.retrievers.fusion import reciprocal_rank_fusion


@register("architecture", "advanced_rag")
class AdvancedRAG(BasePipeline):
    name = "advanced_rag"

    def run(self, query: str) -> RAGResult:
        metrics = RunMetrics()
        traj: list[TrajectoryStep] = []
        cfg = self.c.config
        with timer(metrics):
            queries = [query] + decompose(query, max_subs=2)
            traj.append(TrajectoryStep("multi_query", f"{len(queries)} variants"))

            lists = [helpers.retrieve(self.c, q, cfg.retrieval.k) for q in queries]
            fused = reciprocal_rank_fusion(lists)[: max(cfg.retrieval.k, cfg.reranker.top_n)]
            expanded = helpers.expand_parents(fused)
            traj.append(TrajectoryStep("fuse+expand", f"{len(expanded)} candidates"))

            contexts = helpers.rerank(self.c, query, expanded, cfg.reranker.top_n)
            metrics.retriever_hits = len(contexts)
            resp = helpers.generate(self.c, query, contexts, metrics)
            traj.append(TrajectoryStep("generate", resp.model))

        return RAGResult(query, resp.text, contexts, traj, metrics, self.name)
