"""Tests for the ``/query`` endpoint — auth required, tenant-scoped, offline.

``/query`` must behave like ``/chat`` and ``/documents``: compose the engine
through :mod:`raglab.server.sessions` (tenant-pinned collection) rather than
``build_engine`` against a global collection, and require an authenticated user.
Offline: echo LLM + hashing embedder + temp on-disk Qdrant.
"""

from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    d = tmp_path_factory.mktemp("q")
    os.environ["RAGLAB_APP_DB"] = str(d / "app.db")
    os.environ["RAGLAB_VECTOR_DIR"] = str(d / "qd")
    os.environ["RAGLAB_MEMORY_DB"] = ":memory:"
    os.environ["RAGLAB_MEMORY_QDRANT"] = ":memory:"
    os.environ["RAGLAB_JWT_SECRET"] = "test-secret"
    os.environ.pop("QDRANT_URL", None)

    from fastapi.testclient import TestClient

    from raglab.api import app
    from raglab.server import sessions

    # api.py imports ensure_loaded(), which re-injects QDRANT_URL from .env
    # after the pop above. Re-pop so the suite stays offline.
    os.environ.pop("QDRANT_URL", None)

    sessions.reset_cache()
    return TestClient(app)


def _auth_headers(client, email="q@acme.com"):
    r = client.post(
        "/auth/register",
        json={"email": email, "password": "supersecret", "tenant": "acme"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_query_requires_auth(client):
    r = client.post("/query", json={"query": "x"})
    assert r.status_code == 401


def test_query_offline_answer(client, tmp_path):
    headers = _auth_headers(client, "qans@acme.com")
    doc = tmp_path / "kb.txt"
    doc.write_text("Retrieval fusion merges ranks from multiple searches.", encoding="utf-8")

    r = client.post(
        "/query",
        json={
            "query": "What does retrieval fusion do?",
            "config": "configs/pipelines/naive.yaml",
            "ingest_path": str(doc),
        },
        headers=headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["architecture"]
    assert isinstance(body["answer"], str)
    assert isinstance(body["contexts"], list)
    assert {"latency_ms", "total_tokens", "retriever_hits"} <= body["metrics"].keys()
    assert isinstance(body["trajectory"], list)


def test_query_accepts_inline_overrides(client, tmp_path):
    headers = _auth_headers(client, "qov@acme.com")
    r = client.post(
        "/query",
        json={"query": "hello", "overrides": {"retrieval": {"k": 3}}},
        headers=headers,
    )
    assert r.status_code == 200, r.text