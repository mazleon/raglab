"""GraphRAG interfaces (Phase 2 — Neo4j-backed implementation lands later).

The ``graph_rag`` and ``kg_vector_rag`` architectures are already registered as
stubs in ``raglab.pipelines.stubs``. This module defines the contracts a future
graph store/retriever will implement so the rest of the platform can target them
today.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from raglab.core.types import Document, ScoredChunk


@runtime_checkable
class GraphStore(Protocol):
    """A knowledge graph built from documents (entities + relationships)."""

    def build(self, docs: list[Document]) -> None: ...

    def entity_search(self, query: str, k: int) -> list[ScoredChunk]: ...

    def relationship_search(self, query: str, k: int) -> list[ScoredChunk]: ...

    def multi_hop(self, query: str, hops: int) -> list[ScoredChunk]: ...

    def communities(self) -> list[dict[str, Any]]: ...
