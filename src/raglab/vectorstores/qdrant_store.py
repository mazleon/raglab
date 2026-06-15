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

# Qdrant's embedded (local path) mode takes an exclusive lock on the whole
# directory, so a process may only hold ONE client per path even across
# collections. We therefore cache and share clients keyed by their target
# (server url or on-disk path). ``:memory:`` is deliberately never cached: each
# in-memory client is its own isolated database, which tests rely on.
_CLIENT_CACHE: dict[str, Any] = {}


def build_qdrant_client(
    url: str | None = None, location: str | None = None, timeout: int = 60
) -> Any:
    """Create (or reuse) a QdrantClient with RAGLab's connection precedence (most
    explicit wins): config ``url`` > config ``location`` (``:memory:`` or a path) >
    env ``QDRANT_URL`` > in-memory. An explicit ``location`` beats the ambient
    ``QDRANT_URL`` so ``:memory:`` is never silently redirected to a server.
    Server- and path-backed clients are cached per target so the RAG vector store,
    the memory vector index, and concurrent requests share one connection.
    """

    from qdrant_client import QdrantClient

    api_key = os.environ.get("QDRANT_API_KEY")

    def _cached(key: str, factory: Any) -> Any:
        client = _CLIENT_CACHE.get(key)
        if client is None:
            client = factory()
            _CLIENT_CACHE[key] = client
        return client

    if url:
        return _cached(
            f"url:{url}", lambda: QdrantClient(url=url, api_key=api_key, timeout=timeout)
        )
    if location == ":memory:":
        return QdrantClient(location=":memory:", timeout=timeout)
    if location:
        path = os.path.abspath(location)
        return _cached(f"path:{path}", lambda: QdrantClient(path=path, timeout=timeout))
    if os.environ.get("QDRANT_URL"):
        env_url = os.environ["QDRANT_URL"]
        return _cached(
            f"url:{env_url}", lambda: QdrantClient(url=env_url, api_key=api_key, timeout=timeout)
        )
    return QdrantClient(location=":memory:", timeout=timeout)


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
        self.collection = collection
        self._distance = distance
        self._client = build_qdrant_client(url, location)

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

        conditions: list[Any] = [
            FieldCondition(key=k, match=MatchValue(value=v)) for k, v in where.items()
        ]
        return Filter(must=conditions)

    def search(
        self, vector: Vector, k: int, where: dict[str, Any] | None = None
    ) -> list[ScoredChunk]:
        response = self._client.query_points(
            collection_name=self.collection,
            query=list(vector),
            limit=k,
            query_filter=self._filter(where),
            with_payload=True,
        )
        return [
            ScoredChunk(self._to_chunk(h.payload or {}), float(h.score))
            for h in response.points
        ]

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
