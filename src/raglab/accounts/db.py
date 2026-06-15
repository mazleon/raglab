"""SQLite connection + schema bootstrap for the accounts subsystem.

Plain ``sqlite3`` (no ORM), matching ``raglab.experiments.store``. A single file
holds tenants, users, conversations, and messages. ``WAL`` mode keeps concurrent
reads (the web app) from blocking the writer.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DEFAULT_DB = "reports/raglab_app.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tenants (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    salt          TEXT NOT NULL,
    name          TEXT NOT NULL DEFAULT '',
    tenant_id     TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'member',
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL,
    tenant_id  TEXT NOT NULL,
    title      TEXT NOT NULL DEFAULT 'New chat',
    pipeline   TEXT NOT NULL DEFAULT 'naive',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id              TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role            TEXT NOT NULL,
    content         TEXT NOT NULL,
    metadata_json   TEXT NOT NULL DEFAULT '{}',
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(tenant_id, user_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id, created_at);
"""


def db_path() -> str:
    return os.environ.get("RAGLAB_APP_DB", DEFAULT_DB)


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    """Open a connection with the schema ensured and ``Row`` access."""

    target = Path(path or db_path())
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_SCHEMA)
    return conn


def init_db(path: str | Path | None = None) -> None:
    """Create the schema if absent (idempotent)."""

    connect(path).close()
