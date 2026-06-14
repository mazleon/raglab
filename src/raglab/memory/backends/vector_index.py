"""Qdrant semantic index for memory recall.

A derived, rebuildable projection of the memory records that benefit from
similarity search. Points carry a flat payload (memory_id + scope + type) so
recall can be filtered by type and by tenant/user/agent/session. SQLite remains
the source of truth; this index can be dropped and rebuilt at any time.
"""

from __future__ import annotations

import uuid
from typing import Any

from raglab.core.interfaces import Embedder
from raglab.memory.types import MemoryScope
from raglab.vectorstores.qdrant_store import build_qdrant_client


def _pid(memory_id: str) -> str:
    try:
        return str(uuid.UUID(hex=memory_id))
    except ValueError:
        return str(uuid.uuid5(uuid.NAMESPACE_OID, memory_id))


class MemoryVectorIndex:
    def __init__(
        self,
        embedder: Embedder,
        collection: str = "raglab_memory",
        url: str | None = None,
        location: str | None = None,
    ) -> None:
        self.embedder = embedder
        self.collection = collection
        self._client = build_qdrant_client(url, location)
        self._ensured = False

    def _ensure(self) -> None:
        if self._ensured:
            return
        from qdrant_client.models import Distance, VectorParams

        if not self._client.collection_exists(self.collection):
            self._client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.embedder.dim, distance=Distance.COSINE),
            )
        self._ensured = True

    def upsert(self, memory_id: str, text: str, type_: str, scope: MemoryScope) -> None:
        self._ensure()
        from qdrant_client.models import PointStruct

        vector = self.embedder.embed_documents([text])[0]
        self._client.upsert(
            collection_name=self.collection,
            points=[
                PointStruct(
                    id=_pid(memory_id),
                    vector=list(vector),
                    payload={"memory_id": memory_id, "type": type_, **scope.as_dict()},
                )
            ],
        )

    def _filter(self, scope: MemoryScope, types: list[str] | None):
        from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

        must: list[Any] = []
        for field_name, value in scope.as_dict().items():
            if value:
                must.append(FieldCondition(key=field_name, match=MatchValue(value=value)))
        if types:
            must.append(FieldCondition(key="type", match=MatchAny(any=types)))
        return Filter(must=must) if must else None

    def search(
        self, text: str, k: int, scope: MemoryScope, types: list[str] | None = None
    ) -> list[tuple[str, float]]:
        self._ensure()
        vector = self.embedder.embed_query(text)
        response = self._client.query_points(
            collection_name=self.collection,
            query=list(vector),
            limit=k,
            query_filter=self._filter(scope, types),
            with_payload=True,
        )
        out: list[tuple[str, float]] = []
        for p in response.points:
            mid = (p.payload or {}).get("memory_id")
            if mid:
                out.append((mid, (float(p.score) + 1.0) / 2.0))  # cosine -> [0,1]
        return out

    def delete(self, memory_ids: list[str]) -> None:
        if not memory_ids:
            return
        self._ensure()
        self._client.delete(
            collection_name=self.collection,
            points_selector=[_pid(m) for m in memory_ids],
        )
