"""Per-tenant engine composition against a shared, persistent vector store.

The browser picks an architecture + model + embedding at request time. We load a
base pipeline config, merge those choices in (:mod:`raglab.core.overrides`), then
pin two things server-side that a client must never control:

* **collection** — derived from the tenant + embedding so each tenant's corpus is
  isolated *and* embeddings of different dimensionality never collide in one
  Qdrant collection;
* **vector backend** — a shared Qdrant server (``QDRANT_URL``) or a single on-disk
  path, so a document ingested in one request is retrievable by the next chat
  request (the YAML default of ``:memory:`` would silo every request).

Resolved engines are cached by config signature so repeat chats don't re-build
components or re-open the vector store.
"""

from __future__ import annotations

import os
import re
import threading
from pathlib import Path
from typing import Any

from raglab.core.config import config_from_dict, load_config
from raglab.core.overrides import apply_overrides
from raglab.service import Engine, build_engine

DEFAULT_BASE_CONFIG = "configs/pipelines/naive.yaml"

_PIPELINE_CONFIGS = {
    "naive": "configs/pipelines/naive.yaml",
    "hybrid": "configs/pipelines/hybrid.yaml",
    "agentic": "configs/pipelines/agentic.yaml",
}

# Deterministic default embedding model per provider. Keeps the resolved vector
# dimension (and therefore the collection) stable for the app, and matches the
# models the UI advertises (avoids surprise: OpenAIEmbedder alone defaults to the
# larger 3072-dim model).
_DEFAULT_EMBED_MODELS = {
    "openai": "text-embedding-3-small",
    "cohere": "embed-english-v3.0",
    "gemini": "text-embedding-004",
}

_engine_cache: dict[str, Engine] = {}
_lock = threading.Lock()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "default"


def vector_dir() -> str:
    return os.environ.get("RAGLAB_VECTOR_DIR", "qdrant_storage")


def embedding_dim(embedding_name: str, model: str | None = None, dim: int | None = None) -> int:
    """Resolve an embedder's vector dimension without making a network call.

    Constructing the embedder is cheap (clients are lazy), and reading ``.dim``
    is authoritative — it's exactly what will size/query the collection.
    """

    from raglab.core.config import EmbeddingCfg, build_embedder

    try:
        return int(build_embedder(EmbeddingCfg(name=embedding_name, model=model, dim=dim)).dim)
    except Exception:  # noqa: BLE001 - fall back to a stable bucket if unresolvable
        return 0


def tenant_collection(tenant_id: str, embedding_name: str, dim: int) -> str:
    # The dimension is part of the name so two embeddings of different sizes can
    # never collide in one collection (which would 400 at query time).
    return f"rag_{_slug(tenant_id)}_{_slug(embedding_name)}_{dim}"


def base_config_path(pipeline: str | None) -> str:
    if not pipeline:
        return DEFAULT_BASE_CONFIG
    return _PIPELINE_CONFIGS.get(pipeline, DEFAULT_BASE_CONFIG)


def build_session_config(
    *,
    tenant_id: str,
    pipeline: str | None = None,
    config_path: str | None = None,
    overrides: dict[str, Any] | None = None,
) -> Any:
    """Resolve a fully-validated, tenant-pinned :class:`ExperimentConfig`."""

    cfg = load_config(config_path or base_config_path(pipeline))
    cfg = apply_overrides(cfg, overrides)

    data = cfg.model_dump()

    # Pin a deterministic default model per provider so that document upload and
    # chat — which both compose through here — resolve the SAME model → dim →
    # collection even when the client didn't specify a model.
    if not data["embedding"].get("model"):
        default_model = _DEFAULT_EMBED_MODELS.get(data["embedding"]["name"])
        if default_model:
            data["embedding"]["model"] = default_model

    emb_cfg = data["embedding"]
    dim = embedding_dim(emb_cfg["name"], emb_cfg["model"], emb_cfg["dim"])
    data["collection"] = tenant_collection(tenant_id, emb_cfg["name"], dim)

    qdrant_url = os.environ.get("QDRANT_URL")
    if qdrant_url:
        data["vectorstore"]["url"] = qdrant_url
        data["vectorstore"]["location"] = None
    else:
        # One shared on-disk Qdrant for the whole process (clients are cached
        # per-path in qdrant_store) so ingest + chat see the same vectors.
        data["vectorstore"]["url"] = None
        data["vectorstore"]["location"] = os.path.join(vector_dir(), "rag")
    return config_from_dict(data)


def _signature(cfg: Any) -> str:
    return "|".join(
        str(x)
        for x in (
            cfg.collection,
            cfg.architecture,
            cfg.embedding.name,
            cfg.embedding.model,
            cfg.retrieval.type,
            cfg.retrieval.k,
            cfg.reranker.name,
            cfg.llm.provider,
            cfg.llm.model,
        )
    )


def get_engine(cfg: Any) -> Engine:
    """Return a cached engine for ``cfg``, building one on first use."""

    key = _signature(cfg)
    with _lock:
        engine = _engine_cache.get(key)
        if engine is None:
            engine = build_engine(cfg)
            _engine_cache[key] = engine
        return engine


def ingest_file(cfg: Any, path: str | Path) -> int:
    """Ingest a single file/dir into the tenant collection; returns chunk count."""

    return get_engine(cfg).ingest(path)


def reset_cache() -> None:
    """Drop cached engines (used by tests)."""

    with _lock:
        _engine_cache.clear()
