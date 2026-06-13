"""Optional Neo4j-backed knowledge graph store (requires the ``neo4j`` extra +
NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD).

Same interface as the networkx store. Lazy-imported so the package loads without
the driver installed. Not exercised in offline CI (needs a running Neo4j).
"""

from __future__ import annotations

import os
from typing import Any

from raglab.core.registry import register
from raglab.core.types import Chunk, Document, ScoredChunk
from raglab.graph.extract import extract_entities, extract_relations


@register("graphstore", "neo4j")
class Neo4jGraphStore:
    def __init__(self, **_: object) -> None:
        self._driver = None
        self._chunks: dict[str, Chunk] = {}

    def _ensure(self):
        if self._driver is None:
            try:
                from neo4j import GraphDatabase
            except ImportError as e:  # pragma: no cover
                raise ImportError(
                    "Neo4j backend needs the 'neo4j' extra: pip install 'raglab[neo4j]'"
                ) from e
            self._driver = GraphDatabase.driver(
                os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
                auth=(
                    os.environ.get("NEO4J_USER", "neo4j"),
                    os.environ.get("NEO4J_PASSWORD", "neo4j"),
                ),
            )
        return self._driver

    def build_from_chunks(self, chunks: list[Chunk]) -> None:
        driver = self._ensure()
        with driver.session() as s:
            s.run("MATCH (n) DETACH DELETE n")
            for c in chunks:
                self._chunks[c.chunk_id] = c
                ents = extract_entities(c.text)
                for e in ents:
                    s.run(
                        "MERGE (x:Entity {name:$n}) "
                        "SET x.chunks = coalesce(x.chunks,[]) + $cid",
                        n=e, cid=c.chunk_id,
                    )
                for a, b in extract_relations(ents):
                    s.run(
                        "MATCH (x:Entity {name:$a}),(y:Entity {name:$b}) "
                        "MERGE (x)-[r:CO_OCCURS]->(y) "
                        "SET r.weight = coalesce(r.weight,0)+1",
                        a=a, b=b,
                    )

    def build(self, docs: list[Document]) -> None:  # pragma: no cover
        self.build_from_chunks(
            [Chunk(text=d.text, metadata=d.metadata, document_id=d.document_id) for d in docs]
        )

    def _chunks_for(self, names: list[str], limit: int) -> list[ScoredChunk]:
        driver = self._ensure()
        scores: dict[str, float] = {}
        with driver.session() as s:
            for name in names:
                rec = s.run("MATCH (x:Entity {name:$n}) RETURN x.chunks AS c", n=name)
                for row in rec:
                    for cid in row["c"] or []:
                        scores[cid] = scores.get(cid, 0.0) + 1.0
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return [
            ScoredChunk(self._chunks[cid], sc)
            for cid, sc in ranked[:limit]
            if cid in self._chunks
        ]

    def entity_search(self, query: str, k: int) -> list[ScoredChunk]:
        return self._chunks_for(extract_entities(query) or query.split(), k)

    def relationship_search(self, query: str, k: int) -> list[ScoredChunk]:
        driver = self._ensure()
        names = extract_entities(query) or query.split()
        neighbours = list(names)
        with driver.session() as s:
            for name in names:
                rec = s.run(
                    "MATCH (:Entity {name:$n})-[:CO_OCCURS]-(m) RETURN m.name AS m", n=name
                )
                neighbours.extend(row["m"] for row in rec)
        return self._chunks_for(neighbours, k)

    def multi_hop(self, query: str, hops: int) -> list[ScoredChunk]:
        driver = self._ensure()
        names = extract_entities(query) or query.split()
        reached = set(names)
        with driver.session() as s:
            for name in names:
                rec = s.run(
                    f"MATCH (:Entity {{name:$n}})-[:CO_OCCURS*1..{max(hops, 1)}]-(m) "
                    "RETURN DISTINCT m.name AS m",
                    n=name,
                )
                reached.update(row["m"] for row in rec)
        return self._chunks_for(list(reached), limit=hops * 4 + 4)

    def communities(self) -> list[dict[str, Any]]:  # pragma: no cover
        return []
