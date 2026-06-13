"""GraphRAG: build a knowledge graph from the corpus, retrieve via entity +
multi-hop graph traversal, then generate.

The graph is built from the chunks already in the vector store, so no separate
ingestion is required. Backend (networkx default / neo4j) is config-selectable.
"""

from __future__ import annotations

from raglab.core.registry import create, register
from raglab.core.types import RAGResult, RunMetrics, TrajectoryStep, timer
from raglab.pipelines import helpers
from raglab.pipelines.base import BasePipeline


def build_graph(components):  # type: ignore[no-untyped-def]
    store = create("graphstore", components.config.graph.backend)
    store.build_from_chunks(components.store.all_chunks())
    return store


@register("architecture", "graph_rag")
class GraphRAG(BasePipeline):
    name = "graph_rag"

    def run(self, query: str) -> RAGResult:
        metrics = RunMetrics()
        traj: list[TrajectoryStep] = []
        cfg = self.c.config
        with timer(metrics):
            graph = build_graph(self.c)
            traj.append(
                TrajectoryStep(
                    "build_graph",
                    f"{graph.num_entities} entities, {graph.num_relations} relations",
                )
            )

            entity_hits = graph.entity_search(query, cfg.retrieval.k)
            hop_hits = graph.multi_hop(query, cfg.graph.hops)
            contexts = helpers.dedup(entity_hits + hop_hits)
            traj.append(
                TrajectoryStep(
                    "graph_retrieve",
                    f"{len(entity_hits)} entity + {len(hop_hits)} multi-hop",
                )
            )

            if not contexts:
                # Fall back to vector retrieval if the query had no graph entities.
                contexts = helpers.retrieve(self.c, query, cfg.retrieval.k)
                traj.append(TrajectoryStep("fallback", "vector retrieval"))

            contexts = helpers.rerank(self.c, query, contexts, cfg.reranker.top_n)
            metrics.retriever_hits = len(contexts)
            resp = helpers.generate(self.c, query, contexts, metrics)
            traj.append(TrajectoryStep("generate", resp.model))

        return RAGResult(query, resp.text, contexts, traj, metrics, self.name)
