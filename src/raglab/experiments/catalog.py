"""SQLite experiment store (Phase 5).

Persists every benchmark experiment (config summary + metrics + cost + latency)
so runs accumulate across sessions and power the comparison dashboard.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB = "reports/experiments.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    architecture  TEXT,
    embedding     TEXT,
    retrieval     TEXT,
    reranker      TEXT,
    llm           TEXT,
    n_questions   INTEGER,
    metrics_json  TEXT,
    avg_latency_ms REAL,
    total_cost_usd REAL,
    avg_tokens    REAL,
    timestamp     TEXT
);
"""

_CORE = {
    "experiment_id", "architecture", "embedding", "retrieval", "reranker", "llm",
    "n_questions", "avg_latency_ms", "total_cost_usd", "avg_tokens", "timestamp",
}


def _connect(db_path: str | Path) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    return conn


def save_experiments(rows: list[dict[str, Any]], db_path: str | Path = DEFAULT_DB) -> int:
    conn = _connect(db_path)
    try:
        for row in rows:
            metrics = {k: v for k, v in row.items() if k not in _CORE}
            conn.execute(
                "INSERT OR REPLACE INTO experiments "
                "(experiment_id, architecture, embedding, retrieval, reranker, llm, "
                " n_questions, metrics_json, avg_latency_ms, total_cost_usd, avg_tokens, "
                " timestamp) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    row.get("experiment_id"),
                    row.get("architecture"),
                    row.get("embedding"),
                    row.get("retrieval"),
                    row.get("reranker"),
                    row.get("llm"),
                    row.get("n_questions"),
                    json.dumps(metrics),
                    row.get("avg_latency_ms"),
                    row.get("total_cost_usd"),
                    row.get("avg_tokens"),
                    row.get("timestamp"),
                ),
            )
        conn.commit()
        return len(rows)
    finally:
        conn.close()


def list_experiments(db_path: str | Path = DEFAULT_DB, limit: int = 200) -> list[dict[str, Any]]:
    if not Path(db_path).exists():
        return []
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "SELECT * FROM experiments ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        out: list[dict[str, Any]] = []
        for r in cur.fetchall():
            row = dict(r)
            metrics = json.loads(row.pop("metrics_json") or "{}")
            row.update(metrics)
            out.append(row)
        return out
    finally:
        conn.close()
