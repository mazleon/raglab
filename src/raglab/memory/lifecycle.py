"""Memory lifecycle: TTL expiry, importance decay, pruning, and dedup.

Keeps memory bounded and fresh so it doesn't become silent context-bloat. Runs
against the SQLite source of truth and cascades deletes to the vector index.
"""

from __future__ import annotations

from raglab.memory.backends.sqlite_store import MemorySQLiteStore
from raglab.memory.backends.vector_index import MemoryVectorIndex
from raglab.memory.scoring import decayed_importance
from raglab.memory.types import MemoryScope, _now


class MemoryLifecycle:
    def __init__(self, sqlite: MemorySQLiteStore, index: MemoryVectorIndex | None) -> None:
        self.sqlite = sqlite
        self.index = index

    def _purge(self, ids: list[str], scope: MemoryScope, action: str) -> int:
        for mid in ids:
            self.sqlite.delete(mid)
        if self.index is not None and ids:
            self.index.delete(ids)
        if ids:
            self.sqlite.audit(action, None, scope, f"{len(ids)} records")
        return len(ids)

    def expire_ttl(self) -> int:
        """Delete records past their ``expires_at``."""

        ids = self.sqlite.expired(_now())
        return self._purge(ids, MemoryScope(), "expire")

    def decay(self, scope: MemoryScope, rate_per_day: float = 0.02) -> int:
        """Lower importance with idle time; return number of records updated."""

        updated = 0
        for rec in self.sqlite.query(scope, limit=10000):
            new_imp = decayed_importance(rec.importance, rec.last_accessed_at, rate_per_day)
            if abs(new_imp - rec.importance) > 1e-6:
                self.sqlite.update(rec.id, importance=new_imp)
                updated += 1
        return updated

    def prune_low_importance(self, scope: MemoryScope, threshold: float = 0.1) -> int:
        ids = [
            rec.id for rec in self.sqlite.query(scope, limit=10000)
            if rec.importance < threshold
        ]
        return self._purge(ids, scope, "prune")

    def dedup(self, scope: MemoryScope) -> int:
        """Remove exact-duplicate content within (scope, type), keeping the most
        important copy."""

        best: dict[tuple[str, str], object] = {}
        dupes: list[str] = []
        for rec in self.sqlite.query(scope, limit=10000, order_by="importance"):
            key = (rec.type, rec.content.strip())
            if key in best:
                dupes.append(rec.id)
            else:
                best[key] = rec
        return self._purge(dupes, scope, "dedup")

    def maintain(
        self, scope: MemoryScope, *, decay_rate: float = 0.02, prune_threshold: float = 0.1
    ) -> dict[str, int]:
        return {
            "expired": self.expire_ttl(),
            "deduped": self.dedup(scope),
            "decayed": self.decay(scope, decay_rate),
            "pruned": self.prune_low_importance(scope, prune_threshold),
        }
