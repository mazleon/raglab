"""Lightweight .env loader + provider env-var reconciliation.

We avoid a hard dependency on python-dotenv. ``load_env`` is idempotent and never
overwrites variables already present in the real environment (unless told to).

It also reconciles the variable names used in this project's .env with the names
the underlying SDKs actually read:
    LANGFUSE_BASE_URL  -> LANGFUSE_HOST       (langfuse SDK)
    LANGSMITH_API_KEY  -> LANGCHAIN_API_KEY   (langsmith/langchain)
    LANGFUSE_BASE_URL  -> OPENROUTER fallback handled separately
"""

from __future__ import annotations

import os
from pathlib import Path

_ALIASES = {
    # canonical (SDK-expected) : source name in .env
    "LANGFUSE_HOST": "LANGFUSE_BASE_URL",
    "LANGCHAIN_API_KEY": "LANGSMITH_API_KEY",
}

_loaded = False


def _apply_aliases() -> None:
    for canonical, source in _ALIASES.items():
        if not os.environ.get(canonical) and os.environ.get(source):
            os.environ[canonical] = os.environ[source]
    # LangSmith tracing is enabled if a key is present and not explicitly off.
    if os.environ.get("LANGCHAIN_API_KEY") and not os.environ.get("LANGSMITH_TRACING"):
        os.environ.setdefault("LANGSMITH_TRACING", "true")


def load_env(path: str | Path = ".env", *, override: bool = False) -> None:
    """Load a .env file into os.environ (idempotent)."""

    global _loaded
    p = Path(path)
    if p.exists():
        for raw in p.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if value and (override or key not in os.environ):
                os.environ[key] = value
    _apply_aliases()
    _loaded = True


def ensure_loaded() -> None:
    """Load .env once, on first need, without overriding the real environment."""

    if not _loaded:
        load_env()
