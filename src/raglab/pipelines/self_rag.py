"""Self-RAG.

Emulates Self-RAG reflection tokens with explicit checks:
  ISREL  — filter retrieved docs to those relevant to the query.
  generate over the relevant set.
  ISSUP  — check the answer is supported by that set (grounding).
  ISUSE  — check the answer is non-trivial/useful.
If unsupported, regenerate once constrained to the strongest supporting doc.
"""

from __future__ import annotations

from raglab.agents.critic import critique_answer
from raglab.agents.grading import _content_tokens
from raglab.core.registry import register
from raglab.core.types import RAGResult, RunMetrics, ScoredChunk, TrajectoryStep, timer
from raglab.pipelines import helpers
from raglab.pipelines.base import BasePipeline


def _isrel(query: str, contexts: list[ScoredChunk]) -> list[ScoredChunk]:
    q = _content_tokens(query)
    relevant = [sc for sc in contexts if _content_tokens(sc.text) & q]
    return relevant or contexts[:1]


@register("architecture", "self_rag")
class SelfRAG(BasePipeline):
    name = "self_rag"

    def run(self, query: str) -> RAGResult:
        metrics = RunMetrics()
        traj: list[TrajectoryStep] = []
        cfg = self.c.config
        with timer(metrics):
            retrieved = helpers.retrieve(self.c, query, cfg.retrieval.k)
            relevant = _isrel(query, retrieved)[: cfg.reranker.top_n]
            traj.append(
                TrajectoryStep("ISREL", f"{len(relevant)}/{len(retrieved)} relevant")
            )
            metrics.retriever_hits = len(relevant)

            resp = helpers.generate(self.c, query, relevant, metrics)
            answer = resp.text

            support = critique_answer(query, answer, relevant)
            traj.append(TrajectoryStep("ISSUP", support.reason))
            if not support.ok and relevant:
                metrics.retries = 1
                top = [max(relevant, key=lambda s: s.score)]
                resp = helpers.generate_with_instruction(
                    self.c, query, top,
                    "Answer strictly from the single provided source.", metrics,
                )
                answer = resp.text
                traj.append(TrajectoryStep("regenerate", "constrained to top source"))

            useful = bool(answer.strip()) and not answer.lower().startswith("i don't know")
            traj.append(TrajectoryStep("ISUSE", "useful" if useful else "low utility"))

        return RAGResult(query, answer, relevant, traj, metrics, self.name)
