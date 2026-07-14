"""SQLite-backed registry of ingested documents (per tenant).

Tracks what each tenant has uploaded and its indexing status, so the Knowledge UI
can show real documents, chunk counts, and failures instead of a mock list. The
actual vectors live in Qdrant; this is the human-facing catalog + audit trail.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from raglab.accounts.db import db_path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id           TEXT PRIMARY KEY,
    tenant_id    TEXT NOT NULL,
    name         TEXT NOT NULL,
    type         TEXT NOT NULL DEFAULT '',
    size         INTEGER NOT NULL DEFAULT 0,
    status       TEXT NOT NULL DEFAULT 'pending',
    chunks       INTEGER NOT NULL DEFAULT 0,
    error        TEXT NOT NULL DEFAULT '',
    embedding    TEXT NOT NULL DEFAULT '',
    collection   TEXT NOT NULL DEFAULT '',
    path         TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_docs_tenant ON documents(tenant_id, created_at);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(slots=True)
class DocumentRecord:
    id: str
    tenant_id: str
    name: str
    type: str = ""
    size: int = 0
    status: str = "pending"
    chunks: int = 0
    error: str = ""
    embedding: str = ""
    collection: str = ""
    path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "size": self.size,
            "status": self.status,
            "chunks": self.chunks,
            "error": self.error,
            "embedding": self.embedding,
            "uploaded_at": self.created_at,
        }


def _connect() -> sqlite3.Connection:
    target = Path(db_path())
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA)
    return conn


def create(record: DocumentRecord) -> DocumentRecord:
    record.id = record.id or uuid.uuid4().hex
    record.created_at = record.created_at or _now()
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO documents (id, tenant_id, name, type, size, status, chunks, error, "
            " embedding, collection, path, metadata_json, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (record.id, record.tenant_id, record.name, record.type, record.size,
             record.status, record.chunks, record.error, record.embedding,
             record.collection, record.path, json.dumps(record.metadata), record.created_at),
        )
        conn.commit()
        return record
    finally:
        conn.close()


def update_status(
    doc_id: str, status: str, *, chunks: int | None = None, error: str = ""
) -> None:
    conn = _connect()
    try:
        if chunks is None:
            conn.execute(
                "UPDATE documents SET status = ?, error = ? WHERE id = ?",
                (status, error, doc_id),
            )
        else:
            conn.execute(
                "UPDATE documents SET status = ?, chunks = ?, error = ? WHERE id = ?",
                (status, chunks, error, doc_id),
            )
        conn.commit()
    finally:
        conn.close()


def list_documents(tenant_id: str, limit: int = 500) -> list[DocumentRecord]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM documents WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?",
            (tenant_id, limit),
        ).fetchall()
        return [_row(r) for r in rows]
    finally:
        conn.close()


def get(tenant_id: str, doc_id: str) -> DocumentRecord | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM documents WHERE id = ? AND tenant_id = ?", (doc_id, tenant_id)
        ).fetchone()
        return _row(row) if row else None
    finally:
        conn.close()


def delete(tenant_id: str, doc_id: str) -> bool:
    conn = _connect()
    try:
        cur = conn.execute(
            "DELETE FROM documents WHERE id = ? AND tenant_id = ?", (doc_id, tenant_id)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def _row(r: Any) -> DocumentRecord:
    return DocumentRecord(
        id=r["id"], tenant_id=r["tenant_id"], name=r["name"], type=r["type"],
        size=r["size"], status=r["status"], chunks=r["chunks"], error=r["error"],
        embedding=r["embedding"], collection=r["collection"], path=r["path"],
        metadata=json.loads(r["metadata_json"] or "{}"), created_at=r["created_at"],
    )
