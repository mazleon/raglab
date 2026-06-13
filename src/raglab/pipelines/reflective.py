"""Reflective RAG: generate a draft, reflect on its gaps/groundedness, then
revise once using that reflection as steering."""

from __future__ import annotations

from raglab.agents.critic import critique_answer
from raglab.core.registry import register
from raglab.core.types import RAGResult, RunMetrics, TrajectoryStep, timer
from raglab.pipelines import helpers
from raglab.pipelines.base import BasePipeline


@register("architecture", "reflective_rag")
class ReflectiveRAG(BasePipeline):
    name = "reflective_rag"

    def run(self, query: str) -> RAGResult:
        metrics = RunMetrics()
        traj: list[TrajectoryStep] = []
        cfg = self.c.config
        with timer(metrics):
            candidates = helpers.retrieve(self.c, query, cfg.retrieval.k)
            contexts = helpers.rerank(self.c, query, candidates, cfg.reranker.top_n)
            metrics.retriever_hits = len(contexts)

            draft = helpers.generate(self.c, query, contexts, metrics).text
            traj.append(TrajectoryStep("draft", f"{len(draft)} chars"))

            critique = critique_answer(query, draft, contexts)
            traj.append(TrajectoryStep("reflect", critique.reason))

            if not critique.ok:
                resp = helpers.generate_with_instruction(
                    self.c, query, contexts,
                    f"A previous draft was weak ({critique.reason}). "
                    "Produce an improved, fully grounded answer.",
                    metrics,
                )
                answer = resp.text
                metrics.retries = 1
                traj.append(TrajectoryStep("revise", "regenerated"))
            else:
                answer = draft
                traj.append(TrajectoryStep("accept", "draft accepted"))

        return RAGResult(query, answer, contexts, traj, metrics, self.name)
