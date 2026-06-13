"""Deep Search RAG: iterative breadth-first evidence gathering.

Runs several retrieval rounds. After each round it finds query terms still not
covered by the accumulated context and expands the search with them, broadening
coverage before a final synthesis. Bounded by ``agent.max_retrieval_retries``.
"""

from __future__ import annotations

from raglab.agents.reasoning import identify_gaps
from raglab.core.registry import register
from raglab.core.types import RAGResult, RunMetrics, TrajectoryStep, timer
from raglab.pipelines import helpers
from raglab.pipelines.base import BasePipeline


@register("architecture", "deep_search_rag")
class DeepSearchRAG(BasePipeline):
    name = "deep_search_rag"

    def run(self, query: str) -> RAGResult:
        metrics = RunMetrics()
        traj: list[TrajectoryStep] = []
        cfg = self.c.config
        rounds = max(cfg.agent.max_retrieval_retries, 1) + 1
        with timer(metrics):
            accumulated: list = []
            search_query = query
            for r in range(rounds):
                hits = helpers.retrieve(self.c, search_query, cfg.retrieval.k)
                accumulated = helpers.dedup(accumulated + hits)
                gaps = identify_gaps(query, accumulated)
                traj.append(
                    TrajectoryStep(f"round{r + 1}", f"{len(accumulated)} ctx, gaps={gaps}")
                )
                if not gaps:
                    break
                search_query = query + " " + " ".join(gaps)
                metrics.retries = r + 1

            contexts = helpers.rerank(self.c, query, accumulated, cfg.reranker.top_n + 2)
            metrics.retriever_hits = len(contexts)
            resp = helpers.generate(self.c, query, contexts, metrics)
            traj.append(TrajectoryStep("synthesize", resp.model))

        return RAGResult(query, resp.text, contexts, traj, metrics, self.name)
