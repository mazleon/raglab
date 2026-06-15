"""Capability discovery: which models / embeddings / pipelines the UI may offer.

``available`` is computed from the environment at request time — a provider is
only offered if its API key is actually present — so the frontend never shows a
model the server can't run. Offline options (echo / hashing / local) are always
available, keeping the whole app usable with zero keys.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter

from raglab.core import registry

router = APIRouter(tags=["config"])

# provider -> env var that unlocks it. Absent here == always available (offline).
_PROVIDER_KEYS = {
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "cohere": "COHERE_API_KEY",
}

_MODELS = [
    {"id": "echo", "name": "Echo (Offline)", "provider": "echo",
     "description": "Extractive QA — no LLM key required"},
    {"id": "gpt-4o-mini", "name": "GPT-4o mini", "provider": "openai",
     "description": "Fast, low-cost OpenAI model"},
    {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai",
     "description": "High-capability OpenAI model"},
    {"id": "deepseek/deepseek-chat", "name": "DeepSeek Chat", "provider": "openrouter",
     "description": "Strong open model via OpenRouter"},
    {"id": "qwen/qwen-2.5-72b-instruct", "name": "Qwen 2.5 72B", "provider": "openrouter",
     "description": "Qwen instruct via OpenRouter"},
    {"id": "meta-llama/llama-3.1-70b-instruct", "name": "Llama 3.1 70B", "provider": "openrouter",
     "description": "Meta Llama via OpenRouter"},
    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "provider": "gemini",
     "description": "Google Gemini fast model"},
]

_EMBEDDINGS = [
    {"id": "hashing", "name": "Hashing (Offline)", "provider": "hashing", "dim": 384,
     "description": "Deterministic local hashing — no key required"},
    {"id": "openai", "name": "OpenAI text-embedding-3-small", "provider": "openai", "dim": 1536,
     "description": "OpenAI small embedding"},
    {"id": "cohere", "name": "Cohere embed-english-v3", "provider": "cohere", "dim": 1024,
     "description": "Cohere English embeddings"},
    {"id": "gemini", "name": "Gemini text-embedding-004", "provider": "gemini", "dim": 768,
     "description": "Google Gemini embeddings"},
    {"id": "bge_local", "name": "BGE (Local)", "provider": "local", "dim": 384,
     "description": "Local sentence-transformers (needs the 'local' extra)"},
]

_PIPELINES = [
    {"id": "naive", "name": "Naive RAG", "architecture": "naive_rag",
     "description": "Dense retrieval → generate"},
    {"id": "hybrid", "name": "Hybrid RAG", "architecture": "hybrid_rag",
     "description": "Dense + BM25 fused with RRF → generate"},
    {"id": "agentic", "name": "Agentic RAG", "architecture": "agentic_rag",
     "description": "Self-correcting loop: plan → grade → rewrite → critic → cite"},
]


def _provider_available(provider: str) -> bool:
    key = _PROVIDER_KEYS.get(provider)
    return key is None or bool(os.environ.get(key))


def _mark(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**it, "available": _provider_available(it["provider"])} for it in items]


@router.get("/config/providers")
def providers() -> dict[str, Any]:
    available_providers = {
        p: _provider_available(p) for p in ("echo", "hashing", "local", *_PROVIDER_KEYS)
    }
    try:
        architectures = registry.available("architecture")
    except Exception:  # noqa: BLE001 - never fail discovery
        architectures = ["naive_rag", "hybrid_rag", "agentic_rag"]
    return {
        "providers": available_providers,
        "models": _mark(_MODELS),
        "embeddings": _mark(_EMBEDDINGS),
        "pipelines": _PIPELINES,
        "architectures": architectures,
        "defaults": {"pipeline": "naive", "model": "echo", "embedding": "hashing"},
    }


@router.get("/architectures")
def architectures() -> dict[str, list[str]]:
    return {"architectures": registry.available("architecture")}
