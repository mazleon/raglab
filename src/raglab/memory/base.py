"""BaseMemoryStore — shared implementation over SQLite (+ optional Qdrant).

Concrete memory types subclass this and set ``type`` and ``semantic``. Semantic
stores maintain a vector projection for similarity recall; non-semantic stores
(working / long-term / workflow) recall by recency + importance + structured
filters. Recall ranks by the combined score (relevance · importance · recency).
"""

from __future__ import annotations

from raglab.memory.backends.sqlite_store import MemorySQLiteStore
from raglab.memory.backends.vector_index import MemoryVectorIndex
from raglab.memory.scoring import combined_score, recency_score
from raglab.memory.types import MemoryHit, MemoryQuery, MemoryRecord, MemoryScope, _now


class BaseMemoryStore:
    type: str = "base"
    semantic: bool = True

    def __init__(
        self,
        sqlite: MemorySQLiteStore,
        index: MemoryVectorIndex | None = None,
        **_: object,
    ) -> None:
        self.sqlite = sqlite
        self.index = index

    @property
    def _vectorized(self) -> bool:
        return self.semantic and self.index is not None

    # ---- writes ----
    def add(self, record: MemoryRecord) -> str:
        record.type = self.type
        self.sqlite.add(record)
        if self._vectorized:
            self.index.upsert(record.id, record.content, record.type, record.scope)  # type: ignore[union-attr]
            self.sqlite.update(record.id, embedded=True)
        return record.id

    def update(self, memory_id: str, **changes: object) -> bool:
        changes["updated_at"] = _now()
        ok = self.sqlite.update(memory_id, **changes)
        if ok and self._vectorized and "content" in changes:
            rec = self.sqlite.get(memory_id)
            if rec is not None:
                self.index.upsert(rec.id, rec.content, rec.type, rec.scope)  # type: ignore[union-attr]
        return ok

    def delete(self, memory_id: str) -> bool:
        rec = self.sqlite.get(memory_id)
        ok = self.sqlite.delete(memory_id, rec.scope if rec else None)
        if ok and self._vectorized:
            self.index.delete([memory_id])  # type: ignore[union-attr]
        return ok

    # ---- reads ----
    def get(self, memory_id: str) -> MemoryRecord | None:
        rec = self.sqlite.get(memory_id)
        if rec is not None:
            self.sqlite.touch(memory_id, _now())
        return rec

    def recall(self, query: MemoryQuery) -> list[MemoryHit]:
        """Ranked hits for this memory type."""

        if self._vectorized and query.text.strip():
            pairs = self.index.search(  # type: ignore[union-attr]
                query.text, max(query.k * 3, query.k), query.scope, [self.type]
            )
            relevance = dict(pairs)
            records = self.sqlite.get_many(list(relevance))
            hits = []
            for rec in records:
                if rec.importance < query.min_importance:
                    continue
                rel = relevance.get(rec.id, 0.0)
                rec_score = combined_score(rel, rec.importance, recency_score(rec.last_accessed_at))
                hits.append(MemoryHit(rec, relevance=rel, score=rec_score))
        else:
            records = self.sqlite.query(
                query.scope, types=[self.type], min_importance=query.min_importance,
                limit=max(query.k * 3, query.k), order_by="created_at",
            )
            hits = [
                MemoryHit(
                    rec, relevance=0.0,
                    score=combined_score(0.0, rec.importance, recency_score(rec.last_accessed_at)),
                )
                for rec in records
            ]
        hits.sort(key=lambda h: h.score, reverse=True)
        hits = hits[: query.k]
        for h in hits:
            self.sqlite.touch(h.record.id, _now())
        return hits

    def search(self, query: MemoryQuery) -> list[MemoryRecord]:
        return [h.record for h in self.recall(query)]

    def list(self, scope: MemoryScope, limit: int = 100) -> list[MemoryRecord]:
        return self.sqlite.query(scope, types=[self.type], limit=limit)

    def prune(self, scope: MemoryScope | None = None) -> int:
        """Remove this type's expired (TTL) records. Broader lifecycle policies
        live in ``raglab.memory.lifecycle``."""

        expired = self.sqlite.expired(_now())
        removed = 0
        for mid in expired:
            rec = self.sqlite.get(mid)
            if rec and rec.type == self.type:
                self.delete(mid)
                removed += 1
        return removed
