"""GraphRAG interfaces.

Defines the :class:`GraphStore` contract — a knowledge graph built from chunks
(entities + relationships) — and imports the implementations so they register.
The ``graph_rag`` and ``kg_vector_rag`` architectures consume a registered
graphstore via the composition root.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from raglab.core.types import Chunk, Document, ScoredChunk
from raglab.graph import neo4j_store, store  # noqa: F401  (registers graphstores)


@runtime_checkable
class GraphStore(Protocol):
    """A knowledge graph built from chunks (entities + relationships).

    The real build entry point is :meth:`build_from_chunks` — pipelines call it
    with the vector store's chunks. :meth:`build` is a thin convenience wrapper
    that parses documents to chunks first.
    """

    def build_from_chunks(self, chunks: list[Chunk]) -> None: ...

    def build(self, docs: list[Document]) -> None: ...

    def entity_search(self, query: str, k: int) -> list[ScoredChunk]: ...

    def relationship_search(self, query: str, k: int) -> list[ScoredChunk]: ...

    def multi_hop(self, query: str, hops: int) -> list[ScoredChunk]: ...

    def communities(self) -> list[dict[str, Any]]: ...