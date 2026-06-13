"""Registered stubs for architectures planned in later phases.

They conform to the ``Pipeline`` interface so the registry, config validation,
CLI, and benchmark runner already know about them — implementing one means
replacing its ``run`` body, not wiring new plumbing.
"""

from __future__ import annotations

from raglab.core.registry import register
from raglab.core.types import RAGResult
from raglab.pipelines.base import BasePipeline

# name -> (roadmap phase, one-line description)
_PLANNED: dict[str, tuple[str, str]] = {
    "advanced_rag": ("Phase 3", "query transforms + parent-child expansion + rerank"),
    "crag": ("Phase 3", "Corrective RAG: web/secondary retrieval on low grade"),
    "self_rag": ("Phase 3", "Self-RAG: reflection tokens gate retrieval & critique"),
    "adaptive_rag": ("Phase 3", "router picks strategy by query complexity"),
    "multi_hop_rag": ("Phase 3", "iterative decompose-retrieve-synthesize"),
    "reflective_rag": ("Phase 3", "generate-reflect-revise loop"),
    "deep_search_rag": ("Phase 3", "agentic deep search over many sources"),
    "hierarchical_rag": ("Phase 3", "summary-tree / hierarchical retrieval"),
    "graph_rag": ("Phase 2", "Neo4j entity/relationship graph retrieval"),
    "kg_vector_rag": ("Phase 2", "knowledge-graph + vector hybrid"),
}


def _make_stub(arch_name: str, phase: str, desc: str) -> type:
    class _Stub(BasePipeline):
        name = arch_name

        def run(self, query: str) -> RAGResult:
            raise NotImplementedError(
                f"Architecture {arch_name!r} is planned for {phase}: {desc}. "
                f"It is registered against the Pipeline interface but not yet implemented."
            )

    _Stub.__name__ = f"{arch_name}_stub"
    return _Stub


for _name, (_phase, _desc) in _PLANNED.items():
    register("architecture", _name)(_make_stub(_name, _phase, _desc))
