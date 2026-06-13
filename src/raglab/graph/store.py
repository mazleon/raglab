"""NetworkX-backed knowledge graph store (the in-core GraphRAG default).

Entities are nodes; co-occurrence within a chunk creates weighted edges. Each
entity node records the chunk ids it appears in so graph traversal can return
the underlying text. Community detection uses greedy modularity.
"""

from __future__ import annotations

from typing import Any

import networkx as nx

from raglab.core.registry import register
from raglab.core.types import Chunk, Document, ScoredChunk
from raglab.graph.extract import extract_entities, extract_relations


@register("graphstore", "networkx")
class NetworkXGraphStore:
    def __init__(self, **_: object) -> None:
        self.g = nx.Graph()
        self._chunks: dict[str, Chunk] = {}

    # ---- construction ----
    def _add_chunk(self, chunk: Chunk) -> None:
        self._chunks[chunk.chunk_id] = chunk
        entities = extract_entities(chunk.text)
        for ent in entities:
            if not self.g.has_node(ent):
                self.g.add_node(ent, chunks=set())
            self.g.nodes[ent]["chunks"].add(chunk.chunk_id)
        for a, b in extract_relations(entities):
            w = self.g[a][b]["weight"] + 1 if self.g.has_edge(a, b) else 1
            self.g.add_edge(a, b, weight=w)

    def build(self, docs: list[Document]) -> None:  # pragma: no cover - convenience
        for d in docs:
            self._add_chunk(Chunk(text=d.text, metadata=d.metadata, document_id=d.document_id))

    def build_from_chunks(self, chunks: list[Chunk]) -> None:
        for c in chunks:
            self._add_chunk(c)

    # ---- query ----
    def _match_nodes(self, query: str) -> list[str]:
        q_ents = {e.lower() for e in extract_entities(query)}
        q_words = {w.lower() for w in query.split()}
        matches = []
        for node in self.g.nodes:
            nl = node.lower()
            if nl in q_ents or nl in q_words or any(w in nl for w in q_words if len(w) > 3):
                matches.append(node)
        return matches

    def _chunks_for(self, nodes: list[str], limit: int) -> list[ScoredChunk]:
        scores: dict[str, float] = {}
        for node in nodes:
            for cid in self.g.nodes[node].get("chunks", set()):
                scores[cid] = scores.get(cid, 0.0) + 1.0
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        out = []
        for cid, score in ranked[:limit]:
            if cid in self._chunks:
                out.append(ScoredChunk(self._chunks[cid], score))
        return out

    def entity_search(self, query: str, k: int) -> list[ScoredChunk]:
        return self._chunks_for(self._match_nodes(query), k)

    def relationship_search(self, query: str, k: int) -> list[ScoredChunk]:
        nodes = self._match_nodes(query)
        neighbours: list[str] = list(nodes)
        for node in nodes:
            neighbours.extend(self.g.neighbors(node))
        return self._chunks_for(neighbours, k)

    def multi_hop(self, query: str, hops: int) -> list[ScoredChunk]:
        seeds = self._match_nodes(query)
        reached: set[str] = set(seeds)
        frontier = set(seeds)
        for _ in range(max(hops, 1)):
            nxt: set[str] = set()
            for node in frontier:
                nxt |= set(self.g.neighbors(node))
            frontier = nxt - reached
            reached |= nxt
        return self._chunks_for(list(reached), limit=hops * 4 + 4)

    def communities(self) -> list[dict[str, Any]]:
        if self.g.number_of_nodes() == 0:
            return []
        comms = nx.community.greedy_modularity_communities(self.g)
        return [{"id": i, "members": sorted(c)} for i, c in enumerate(comms)]

    @property
    def num_entities(self) -> int:
        return self.g.number_of_nodes()

    @property
    def num_relations(self) -> int:
        return self.g.number_of_edges()
