"""Qdrant vector store adapter.

Runs in-memory (``location: ":memory:"``) for tests or against a server
(``url`` / ``QDRANT_URL``). Chunk text + metadata travel in the point payload so
retrieval reconstructs full :class:`Chunk` objects, and ``all_chunks`` supports
the BM25 retriever.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from raglab.core.registry import register
from raglab.core.types import Chunk, ScoredChunk, Vector

_DISTANCE = {"cosine": "Cosine", "dot": "Dot", "euclid": "Euclid"}


def _point_id(chunk_id: str) -> str:
    try:
        return str(uuid.UUID(hex=chunk_id))
    except ValueError:
        return str(uuid.uuid5(uuid.NAMESPACE_OID, chunk_id))


@register("vectorstore", "qdrant")
class QdrantStore:
    def __init__(
        self,
        collection: str,
        url: str | None = None,
        location: str | None = None,
        distance: str = "cosine",
        **_: object,
    ) -> None:
        from qdrant_client import QdrantClient

        self.collection = collection
        self._distance = distance
        url = url or os.environ.get("QDRANT_URL")
        if url:
            self._client = QdrantClient(
                url=url, api_key=os.environ.get("QDRANT_API_KEY")
            )
        else:
            # Default to a persistent local server is undesirable for tests, so
            # fall back to in-memory unless a location/url is explicitly given.
            self._client = QdrantClient(location=location or ":memory:")

    def ensure_collection(self, dim: int) -> None:
        from qdrant_client.models import Distance, VectorParams

        dist = Distance[_DISTANCE.get(self._distance, "Cosine").upper()]
        if self._client.collection_exists(self.collection):
            return
        self._client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(size=dim, distance=dist),
        )

    def upsert(self, chunks: list[Chunk], vectors: list[Vector]) -> None:
        from qdrant_client.models import PointStruct

        points = [
            PointStruct(
                id=_point_id(c.chunk_id),
                vector=list(v),
                payload={
                    "text": c.text,
                    "chunk_id": c.chunk_id,
                    "document_id": c.document_id,
                    "metadata": c.metadata,
                },
            )
            for c, v in zip(chunks, vectors, strict=True)
        ]
        self._client.upsert(collection_name=self.collection, points=points)

    def _to_chunk(self, payload: dict[str, Any]) -> Chunk:
        return Chunk(
            text=payload.get("text", ""),
            metadata=payload.get("metadata", {}) or {},
            chunk_id=payload.get("chunk_id", ""),
            document_id=payload.get("document_id", ""),
        )

    def _filter(self, where: dict[str, Any] | None):
        if not where:
            return None
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        conditions = [
            FieldCondition(key=k, match=MatchValue(value=v)) for k, v in where.items()
        ]
        return Filter(must=conditions)

    def search(
        self, vector: Vector, k: int, where: dict[str, Any] | None = None
    ) -> list[ScoredChunk]:
        hits = self._client.search(
            collection_name=self.collection,
            query_vector=list(vector),
            limit=k,
            query_filter=self._filter(where),
            with_payload=True,
        )
        return [ScoredChunk(self._to_chunk(h.payload or {}), float(h.score)) for h in hits]

    def all_chunks(self) -> list[Chunk]:
        out: list[Chunk] = []
        offset = None
        while True:
            points, offset = self._client.scroll(
                collection_name=self.collection,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            out.extend(self._to_chunk(p.payload or {}) for p in points)
            if offset is None:
                break
        return out
