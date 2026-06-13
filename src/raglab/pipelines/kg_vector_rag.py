"""Knowledge-Graph + Vector hybrid RAG.

Fuses graph traversal results with dense/hybrid vector retrieval via RRF, getting
both the relational structure of GraphRAG and the semantic recall of vector
search, then reranks and generates.
"""

from __future__ import annotations

from raglab.core.registry import register
from raglab.core.types import RAGResult, RunMetrics, TrajectoryStep, timer
from raglab.pipelines import helpers
from raglab.pipelines.base import BasePipeline
from raglab.pipelines.graph_rag import build_graph
from raglab.retrievers.fusion import reciprocal_rank_fusion


@register("architecture", "kg_vector_rag")
class KGVectorRAG(BasePipeline):
    name = "kg_vector_rag"

    def run(self, query: str) -> RAGResult:
        metrics = RunMetrics()
        traj: list[TrajectoryStep] = []
        cfg = self.c.config
        with timer(metrics):
            graph = build_graph(self.c)
            graph_hits = helpers.dedup(
                graph.entity_search(query, cfg.retrieval.k)
                + graph.multi_hop(query, cfg.graph.hops)
            )
            vector_hits = helpers.retrieve(self.c, query, cfg.retrieval.k)
            traj.append(
                TrajectoryStep(
                    "dual_retrieve", f"{len(graph_hits)} graph + {len(vector_hits)} vector"
                )
            )

            fused = reciprocal_rank_fusion([graph_hits, vector_hits], cfg.retrieval.rrf_k)
            contexts = helpers.rerank(self.c, query, fused, cfg.reranker.top_n)
            metrics.retriever_hits = len(contexts)
            resp = helpers.generate(self.c, query, contexts, metrics)
            traj.append(TrajectoryStep("generate", resp.model))

        return RAGResult(query, resp.text, contexts, traj, metrics, self.name)
