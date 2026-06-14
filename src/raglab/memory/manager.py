"""MemoryManager — the single entrypoint to the Memory Engineering Platform.

Wires the SQLite source of truth + Qdrant semantic index + the ten memory stores,
and exposes remember / recall (cross-type, fused) / forget / consolidate /
timeline / stats / maintain, plus scope-based governance (tenant isolation, GDPR
erase, audit). Storage is offline by default (SQLite ``:memory:`` + in-memory
Qdrant + hashing embedder) and swappable for production backends.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from raglab.core import registry
from raglab.core.interfaces import Embedder
from raglab.memory.backends.sqlite_store import MemorySQLiteStore
from raglab.memory.backends.vector_index import MemoryVectorIndex
from raglab.memory.formation import MemoryFormationEngine
from raglab.memory.interfaces import MemoryStore
from raglab.memory.lifecycle import MemoryLifecycle
from raglab.memory.scoring import importance_from_signals
from raglab.memory.types import (
    MEMORY_TYPES,
    MemoryHit,
    MemoryQuery,
    MemoryRecord,
    MemoryScope,
    now_dt,
)

# Types worth searching for a free-text query (semantic projections exist).
SEMANTIC_TYPES = ("episodic", "semantic", "procedural", "reflection", "agent", "shared", "graph")


class MemoryManager:
    def __init__(
        self,
        embedder: Embedder | None = None,
        *,
        db_path: str = ":memory:",
        qdrant_location: str = ":memory:",
        collection: str = "raglab_memory",
        formation: MemoryFormationEngine | None = None,
    ) -> None:
        registry.bootstrap()
        if embedder is None:
            embedder = registry.create("embedder", "hashing", dim=256)
        self.embedder = embedder
        self.sqlite = MemorySQLiteStore(db_path)
        self.index = MemoryVectorIndex(embedder, collection, location=qdrant_location)
        self.stores: dict[str, MemoryStore] = {
            t: registry.create("memory", t, sqlite=self.sqlite, index=self.index)
            for t in MEMORY_TYPES
        }
        self.formation = formation or MemoryFormationEngine()
        self.lifecycle = MemoryLifecycle(self.sqlite, self.index)

    # ---- access ----
    def store(self, type_: str) -> MemoryStore:
        if type_ not in self.stores:
            from raglab.errors import ConfigError

            raise ConfigError(
                f"Unknown memory type {type_!r}. Valid: {', '.join(MEMORY_TYPES)}"
            )
        return self.stores[type_]

    # ---- writes ----
    def remember(
        self,
        type_: str,
        content: str,
        scope: MemoryScope,
        *,
        importance: float | None = None,
        structured: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        ttl_seconds: int | None = None,
        force: bool = False,
    ) -> str | None:
        """Store a memory if the formation engine deems it worth keeping.

        Returns the new id, or ``None`` if formation chose to forget it.
        """

        imp = importance_from_signals(content, explicit=importance)
        if not force and not self.formation.should_remember(content, imp):
            return None
        rec = MemoryRecord(
            content=content, type=type_, scope=scope, importance=imp,
            metadata=metadata or {}, structured=structured or {},
        )
        if ttl_seconds:
            rec.expires_at = (now_dt() + timedelta(seconds=ttl_seconds)).isoformat()
        return self.store(type_).add(rec)

    def forget(self, memory_id: str) -> bool:
        rec = self.sqlite.get(memory_id)
        if rec is None:
            return False
        return self.store(rec.type).delete(memory_id)

    # ---- reads ----
    def recall(
        self, query: MemoryQuery, types: list[str] | None = None
    ) -> list[MemoryHit]:
        """Cross-type recall, fused and ranked by combined score."""

        search_types = types or query.types or list(SEMANTIC_TYPES)
        hits: list[MemoryHit] = []
        for t in search_types:
            if t in self.stores:
                hits.extend(self.stores[t].recall(query))  # type: ignore[attr-defined]
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[: query.k]

    def timeline(
        self, scope: MemoryScope, since: str | None = None, until: str | None = None,
        limit: int = 200,
    ) -> list[MemoryRecord]:
        return self.sqlite.query(scope, since=since, until=until, limit=limit)

    def stats(self, scope: MemoryScope) -> dict[str, Any]:
        return self.sqlite.stats(scope)

    def audit(self, scope: MemoryScope, limit: int = 100) -> list[dict[str, Any]]:
        return self.sqlite.audit_log(scope, limit)

    # ---- consolidation + maintenance ----
    def consolidate(self, scope: MemoryScope, max_items: int = 25) -> str | None:
        """Summarize recent working + episodic memory into a durable long-term
        record (short-term -> long-term consolidation)."""

        recent = self.sqlite.query(
            scope, types=["working", "episodic"], limit=max_items, order_by="created_at"
        )
        if not recent:
            return None
        lines = [f"- {r.content.splitlines()[0][:160]}" for r in recent]
        summary = "Consolidated session memory:\n" + "\n".join(lines)
        return self.remember(
            "long_term", summary, scope, importance=0.85,
            structured={"consolidated_from": [r.id for r in recent]}, force=True,
        )

    def maintain(self, scope: MemoryScope, **kw: Any) -> dict[str, int]:
        return self.lifecycle.maintain(scope, **kw)

    def erase(self, scope: MemoryScope) -> int:
        """GDPR erase: delete every record in scope from SQLite + the vector index."""

        ids = [r.id for r in self.sqlite.query(scope, limit=100000)]
        removed = self.sqlite.delete_scope(scope)
        self.index.delete(ids)
        return removed

    def close(self) -> None:
        self.sqlite.close()
