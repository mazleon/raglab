"""Corrective RAG (CRAG).

Retrieve -> grade. On a confident-correct grade, refine (strip to the most
relevant sentences) and generate. On a low grade, take a corrective action:
rewrite the query and re-retrieve more broadly (the offline analogue of CRAG's
web/secondary knowledge fallback), then generate over the combined evidence.
"""

from __future__ import annotations

from raglab.agents.grading import _content_tokens, grade_retrieval
from raglab.agents.rewrite import rewrite_query
from raglab.core.registry import register
from raglab.core.types import Chunk, RAGResult, RunMetrics, ScoredChunk, TrajectoryStep, timer
from raglab.pipelines import helpers
from raglab.pipelines.base import BasePipeline


def _refine(query: str, contexts: list[ScoredChunk]) -> list[ScoredChunk]:
    """Knowledge refinement: keep only sentences overlapping the query."""

    q = _content_tokens(query)
    refined: list[ScoredChunk] = []
    for sc in contexts:
        sents = [s for s in sc.text.split(". ") if _content_tokens(s) & q]
        text = ". ".join(sents) if sents else sc.text
        refined.append(ScoredChunk(Chunk(text, sc.chunk.metadata, sc.chunk.chunk_id,
                                          sc.chunk.document_id), sc.score))
    return refined


@register("architecture", "crag")
class CorrectiveRAG(BasePipeline):
    name = "crag"

    def run(self, query: str) -> RAGResult:
        metrics = RunMetrics()
        traj: list[TrajectoryStep] = []
        cfg = self.c.config
        threshold = cfg.agent.grade_threshold
        with timer(metrics):
            contexts = helpers.retrieve(self.c, query, cfg.retrieval.k)
            grade = grade_retrieval(query, contexts)
            traj.append(TrajectoryStep("grade", f"score={grade.score}"))

            if grade.score < threshold:
                # Corrective action: rewrite + broaden retrieval.
                new_q = rewrite_query(query, 1)
                extra = helpers.retrieve(self.c, new_q, cfg.retrieval.k * 2)
                contexts = helpers.dedup(contexts + extra)
                metrics.retries = 1
                traj.append(TrajectoryStep("correct", f"rewrote -> {len(contexts)} ctx"))
            else:
                traj.append(TrajectoryStep("accept", "retrieval correct"))

            contexts = _refine(query, contexts)[: cfg.reranker.top_n]
            metrics.retriever_hits = len(contexts)
            resp = helpers.generate(self.c, query, contexts, metrics)
            traj.append(TrajectoryStep("generate", resp.model))

        return RAGResult(query, resp.text, contexts, traj, metrics, self.name)
