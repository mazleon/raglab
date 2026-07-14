"""Tests for the enterprise chatbot layer: overrides, auth, conversations, API.

All offline — echo LLM + hashing embedder + temp SQLite + temp on-disk Qdrant,
so no API keys are required.
"""

from __future__ import annotations

import os

import pytest


# --------------------------------------------------------------------------- #
# Config overrides (pure unit)
# --------------------------------------------------------------------------- #
def test_apply_overrides_deep_merge():
    from raglab.core.config import load_config
    from raglab.core.overrides import apply_overrides

    base = load_config("configs/pipelines/naive.yaml")
    merged = apply_overrides(
        base, {"llm": {"provider": "openai", "model": "gpt-4o-mini"}, "retrieval": {"k": 9}}
    )
    assert merged.llm.provider == "openai"
    assert merged.llm.model == "gpt-4o-mini"
    assert merged.retrieval.k == 9
    # untouched fields survive the merge
    assert merged.embedding.name == base.embedding.name


def test_apply_overrides_rejects_bad_embedding():
    from raglab.core.config import load_config
    from raglab.core.overrides import apply_overrides
    from raglab.errors import ConfigError

    base = load_config("configs/pipelines/naive.yaml")
    with pytest.raises(ConfigError):
        apply_overrides(base, {"embedding": {"name": "openrouter"}})


def test_overrides_clear_stale_embedding_dim_on_provider_switch():
    """Switching embedding provider must not inherit the base provider's dim/model
    (the bug that sized a 384-dim collection then queried it with 3072-dim vectors)."""
    from raglab.core.config import load_config
    from raglab.core.overrides import apply_overrides

    base = load_config("configs/pipelines/hybrid.yaml")  # hashing, dim 384
    assert base.embedding.name == "hashing" and base.embedding.dim == 384
    merged = apply_overrides(base, {"embedding": {"name": "openai"}})
    assert merged.embedding.name == "openai"
    assert merged.embedding.dim is None  # 384 must NOT leak
    assert merged.embedding.model is None


def test_session_config_pins_model_and_dim_aware_collection():
    from raglab.server.sessions import build_session_config

    # Offline default: hashing → dim-suffixed collection.
    naive = build_session_config(tenant_id="acme", pipeline="naive", overrides={})
    assert naive.collection == "rag_acme_hashing_384"

    # Provider switch resolves a deterministic model + its native dim (1536),
    # never the leaked 384 — so upload and chat agree.
    openai = build_session_config(
        tenant_id="acme", pipeline="hybrid", overrides={"embedding": {"name": "openai"}}
    )
    assert openai.embedding.model == "text-embedding-3-small"
    assert openai.collection == "rag_acme_openai_1536"


def test_sanitize_overrides_drops_unknown_keys():
    from raglab.core.overrides import sanitize_overrides

    clean = sanitize_overrides(
        {"llm": {"provider": "echo"}, "observability": {"langfuse": True}, "bogus": 1}
    )
    assert clean == {"llm": {"provider": "echo"}}


# --------------------------------------------------------------------------- #
# Auth (password hashing + JWT)
# --------------------------------------------------------------------------- #
def test_password_hash_roundtrip():
    from raglab.accounts.auth import hash_password, verify_password

    h, salt = hash_password("hunter2hunter2")
    assert verify_password("hunter2hunter2", h, salt)
    assert not verify_password("wrong", h, salt)


def test_jwt_roundtrip_and_tamper(monkeypatch):
    monkeypatch.setenv("RAGLAB_JWT_SECRET", "unit-secret")
    from raglab.accounts.auth import User, decode_token, issue_token
    from raglab.errors import AuthError

    user = User(id="u1", email="a@b.com", name="A", tenant_id="acme", role="owner")
    token = issue_token(user)
    decoded = decode_token(token)
    assert decoded.id == "u1" and decoded.tenant_id == "acme"
    with pytest.raises(AuthError):
        decode_token(token + "x")


# --------------------------------------------------------------------------- #
# API integration (TestClient, offline)
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def client(tmp_path_factory):
    d = tmp_path_factory.mktemp("ent")
    os.environ["RAGLAB_APP_DB"] = str(d / "app.db")
    os.environ["RAGLAB_VECTOR_DIR"] = str(d / "qd")
    os.environ["RAGLAB_MEMORY_DB"] = ":memory:"
    os.environ["RAGLAB_MEMORY_QDRANT"] = ":memory:"
    os.environ["RAGLAB_JWT_SECRET"] = "test-secret"
    os.environ.pop("QDRANT_URL", None)  # force local on-disk store

    from fastapi.testclient import TestClient

    from raglab.api import app
    from raglab.server import sessions

    # api.py calls ensure_loaded() at import, which re-injects QDRANT_URL from
    # .env (cloud) *after* the pop above. Re-pop now that .env is loaded so the
    # suite stays offline (ensure_loaded is idempotent — won't reload).
    os.environ.pop("QDRANT_URL", None)

    sessions.reset_cache()
    return TestClient(app)


def _auth_headers(client, email="leon@acme.com"):
    r = client.post(
        "/auth/register",
        json={"email": email, "password": "supersecret", "tenant": "acme"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_config_providers_offline_available(client):
    data = client.get("/config/providers").json()
    assert data["providers"]["echo"] is True
    assert data["providers"]["hashing"] is True
    assert any(m["id"] == "echo" and m["available"] for m in data["models"])


def test_auth_required(client):
    assert client.get("/conversations").status_code == 401


def test_duplicate_registration_rejected(client):
    client.post("/auth/register", json={"email": "dup@x.com", "password": "supersecret"})
    r = client.post("/auth/register", json={"email": "dup@x.com", "password": "supersecret"})
    assert r.status_code == 401


def test_conversation_crud(client):
    headers = _auth_headers(client, "conv@acme.com")
    created = client.post("/conversations", json={"title": "T1"}, headers=headers).json()
    cid = created["id"]
    listed = client.get("/conversations", headers=headers).json()
    assert any(c["id"] == cid for c in listed["conversations"])
    got = client.get(f"/conversations/{cid}", headers=headers).json()
    assert got["title"] == "T1" and got["messages"] == []
    assert client.delete(f"/conversations/{cid}", headers=headers).json()["deleted"]


def test_chat_stream_offline(client):
    headers = _auth_headers(client, "chat@acme.com")
    r = client.post(
        "/chat/stream",
        json={"query": "What is RRF?", "pipeline": "naive"},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.text
    # ordered SSE events present
    assert "event: meta" in body
    assert "event: metrics" in body
    assert "event: done" in body
    # the user turn was persisted into a fresh conversation
    convs = client.get("/conversations", headers=headers).json()["conversations"]
    assert convs


def test_tenant_isolation(client):
    a = _auth_headers(client, "iso-a@acme.com")
    b = _auth_headers(client, "iso-b@other.com")
    cid = client.post("/conversations", json={"title": "secret"}, headers=a).json()["id"]
    # user B (different tenant) cannot see or fetch A's conversation
    assert client.get(f"/conversations/{cid}", headers=b).status_code == 401
    b_list = client.get("/conversations", headers=b).json()["conversations"]
    assert all(c["id"] != cid for c in b_list)
