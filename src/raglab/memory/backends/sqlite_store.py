"""SQLite structured memory store — the source of truth.

Holds every :class:`MemoryRecord` as a row with scope columns for tenant/user/
agent/session isolation, plus an append-only audit log for governance. Exact and
filtered queries, recency, TTL expiry, temporal timelines, stats, and GDPR
delete-by-scope all live here. Semantic recall is layered on top via Qdrant.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

from raglab.memory.types import MemoryRecord, MemoryScope

_SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    content TEXT NOT NULL,
    structured TEXT NOT NULL,
    metadata TEXT NOT NULL,
    importance REAL NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_accessed_at TEXT NOT NULL,
    access_count INTEGER NOT NULL,
    expires_at TEXT,
    embedded INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mem_scope ON memories(tenant_id, user_id, type);
CREATE INDEX IF NOT EXISTS idx_mem_session ON memories(session_id);
CREATE INDEX IF NOT EXISTS idx_mem_expires ON memories(expires_at);

CREATE TABLE IF NOT EXISTS memory_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id TEXT,
    action TEXT NOT NULL,
    tenant_id TEXT,
    user_id TEXT,
    agent_id TEXT,
    session_id TEXT,
    detail TEXT,
    ts TEXT NOT NULL
);
"""

_COLS = [
    "id", "type", "tenant_id", "user_id", "agent_id", "session_id", "content",
    "structured", "metadata", "importance", "created_at", "updated_at",
    "last_accessed_at", "access_count", "expires_at", "embedded",
]


class MemorySQLiteStore:
    def __init__(self, path: str = ":memory:") -> None:
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

    # ---- (de)serialization ----
    @staticmethod
    def _to_row(r: MemoryRecord) -> tuple:
        return (
            r.id, r.type, r.scope.tenant_id, r.scope.user_id, r.scope.agent_id,
            r.scope.session_id, r.content, json.dumps(r.structured),
            json.dumps(r.metadata), r.importance, r.created_at, r.updated_at,
            r.last_accessed_at, r.access_count, r.expires_at, int(r.embedded),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            content=row["content"],
            type=row["type"],
            scope=MemoryScope(
                tenant_id=row["tenant_id"], user_id=row["user_id"],
                agent_id=row["agent_id"], session_id=row["session_id"],
            ),
            importance=row["importance"],
            metadata=json.loads(row["metadata"]),
            structured=json.loads(row["structured"]),
            id=row["id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_accessed_at=row["last_accessed_at"],
            access_count=row["access_count"],
            expires_at=row["expires_at"],
            embedded=bool(row["embedded"]),
        )

    # ---- writes ----
    def add(self, record: MemoryRecord) -> str:
        ph = ",".join(["?"] * len(_COLS))
        with self._lock:
            self._conn.execute(
                f"INSERT OR REPLACE INTO memories ({','.join(_COLS)}) VALUES ({ph})",
                self._to_row(record),
            )
            self._conn.commit()
        self.audit("create", record.id, record.scope, record.type)
        return record.id

    def update(self, memory_id: str, **changes: Any) -> bool:
        allowed = {
            "content", "importance", "metadata", "structured", "updated_at",
            "last_accessed_at", "access_count", "expires_at", "embedded",
        }
        sets, vals = [], []
        for k, v in changes.items():
            if k not in allowed:
                continue
            if k in ("metadata", "structured"):
                v = json.dumps(v)
            if k == "embedded":
                v = int(v)
            sets.append(f"{k}=?")
            vals.append(v)
        if not sets:
            return False
        vals.append(memory_id)
        with self._lock:
            cur = self._conn.execute(
                f"UPDATE memories SET {','.join(sets)} WHERE id=?", vals
            )
            self._conn.commit()
            return cur.rowcount > 0

    def touch(self, memory_id: str, when: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE memories SET last_accessed_at=?, access_count=access_count+1 "
                "WHERE id=?",
                (when, memory_id),
            )
            self._conn.commit()

    def delete(self, memory_id: str, scope: MemoryScope | None = None) -> bool:
        with self._lock:
            cur = self._conn.execute("DELETE FROM memories WHERE id=?", (memory_id,))
            self._conn.commit()
            deleted = cur.rowcount > 0
        if deleted:
            self.audit("delete", memory_id, scope or MemoryScope(), "single")
        return deleted

    def delete_scope(self, scope: MemoryScope) -> int:
        """GDPR erase: remove every record matching the (non-empty) scope fields."""

        where, params = self._scope_where(scope, require_any=True)
        ids = [
            r["id"]
            for r in self._select(f"SELECT id FROM memories WHERE {where}", tuple(params))
        ]
        with self._lock:
            self._conn.execute(f"DELETE FROM memories WHERE {where}", params)
            self._conn.commit()
        self.audit("erase", None, scope, f"{len(ids)} records")
        return len(ids)

    # ---- reads ----
    def get(self, memory_id: str) -> MemoryRecord | None:
        rows = self._select("SELECT * FROM memories WHERE id=?", (memory_id,))
        return self._from_row(rows[0]) if rows else None

    def get_many(self, ids: list[str]) -> list[MemoryRecord]:
        if not ids:
            return []
        ph = ",".join(["?"] * len(ids))
        rows = self._select(f"SELECT * FROM memories WHERE id IN ({ph})", tuple(ids))
        by_id = {r["id"]: self._from_row(r) for r in rows}
        return [by_id[i] for i in ids if i in by_id]

    def query(
        self,
        scope: MemoryScope,
        types: list[str] | None = None,
        min_importance: float = 0.0,
        limit: int = 100,
        since: str | None = None,
        until: str | None = None,
        order_by: str = "created_at",
    ) -> list[MemoryRecord]:
        where, params = self._scope_where(scope)
        clauses = [where, "importance >= ?"]
        params.append(min_importance)
        if types:
            clauses.append(f"type IN ({','.join(['?'] * len(types))})")
            params.extend(types)
        if since:
            clauses.append("created_at >= ?")
            params.append(since)
        if until:
            clauses.append("created_at <= ?")
            params.append(until)
        valid_order = ("created_at", "importance", "last_accessed_at")
        order = order_by if order_by in valid_order else "created_at"
        sql = (
            f"SELECT * FROM memories WHERE {' AND '.join(clauses)} "
            f"ORDER BY {order} DESC LIMIT ?"
        )
        params.append(limit)
        return [self._from_row(r) for r in self._select(sql, tuple(params))]

    def expired(self, now_iso: str) -> list[str]:
        rows = self._select(
            "SELECT id FROM memories WHERE expires_at IS NOT NULL AND expires_at <= ?",
            (now_iso,),
        )
        return [r["id"] for r in rows]

    def stats(self, scope: MemoryScope) -> dict[str, Any]:
        where, params = self._scope_where(scope)
        rows = self._select(
            f"SELECT type, COUNT(*) n, AVG(importance) imp FROM memories "
            f"WHERE {where} GROUP BY type",
            tuple(params),
        )
        by_type = {r["type"]: {"count": r["n"], "avg_importance": round(r["imp"] or 0, 3)}
                   for r in rows}
        total = sum(v["count"] for v in by_type.values())
        return {"total": total, "by_type": by_type}

    # ---- audit ----
    def audit(
        self, action: str, memory_id: str | None, scope: MemoryScope, detail: str
    ) -> None:
        from raglab.memory.types import _now

        with self._lock:
            self._conn.execute(
                "INSERT INTO memory_audit "
                "(memory_id, action, tenant_id, user_id, agent_id, session_id, detail, ts) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (memory_id, action, scope.tenant_id, scope.user_id, scope.agent_id,
                 scope.session_id, detail, _now()),
            )
            self._conn.commit()

    def audit_log(self, scope: MemoryScope, limit: int = 100) -> list[dict[str, Any]]:
        where, params = self._scope_where(scope)
        rows = self._select(
            f"SELECT * FROM memory_audit WHERE {where} ORDER BY id DESC LIMIT ?",
            (*params, limit),
        )
        return [dict(r) for r in rows]

    # ---- helpers ----
    def _select(self, sql: str, params: tuple) -> list[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    @staticmethod
    def _scope_where(scope: MemoryScope, require_any: bool = False) -> tuple[str, list]:
        """Equality on every non-empty scope field (empty = wildcard)."""

        clauses, params = [], []
        for field_name, value in scope.as_dict().items():
            if value:
                clauses.append(f"{field_name}=?")
                params.append(value)
        if not clauses:
            if require_any:
                raise ValueError("refusing to erase with an empty scope")
            return "1=1", params
        return " AND ".join(clauses), params

    def close(self) -> None:
        with self._lock:
            self._conn.close()
