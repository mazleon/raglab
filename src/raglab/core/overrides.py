"""Apply runtime config overrides onto a base :class:`ExperimentConfig`.

The frontend lets a user pick an architecture / LLM / embedding / retriever at
request time. Rather than write a YAML file per request, the API loads a base
config and deep-merges a small override dict onto it, then re-validates through
the same composition root (so every guard — e.g. the embedding allow-list — still
fires). Swapping a component remains a config edit; this just moves the edit
in-memory.
"""

from __future__ import annotations

from typing import Any

from raglab.core.config import ExperimentConfig, config_from_dict

# Only these top-level sections may be overridden from an untrusted client. This
# is an allow-list on purpose: it keeps request payloads from reaching into
# observability/evaluation/vectorstore internals.
_ALLOWED_SECTIONS = {
    "architecture",
    "collection",
    "llm",
    "embedding",
    "retrieval",
    "reranker",
    "chunker",
    "agent",
}


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``patch`` into a copy of ``base`` (patch wins)."""

    out = dict(base)
    for key, value in patch.items():
        if value is None:
            continue
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def sanitize_overrides(overrides: dict[str, Any] | None) -> dict[str, Any]:
    """Drop any keys outside the allow-list and any empty leaf values."""

    if not overrides:
        return {}
    clean: dict[str, Any] = {}
    for key, value in overrides.items():
        if key not in _ALLOWED_SECTIONS or value is None:
            continue
        if isinstance(value, dict):
            inner = {k: v for k, v in value.items() if v is not None and v != ""}
            if inner:
                clean[key] = inner
        elif value != "":
            clean[key] = value
    return clean


def apply_overrides(
    base: ExperimentConfig, overrides: dict[str, Any] | None
) -> ExperimentConfig:
    """Return a new validated config with ``overrides`` merged onto ``base``.

    Re-validation reuses :func:`config_from_dict`, so a bad override (e.g.
    ``embedding.name: openrouter``) raises the same ``ConfigError`` the YAML path
    would — surfaced by the API as a 400.
    """

    clean = sanitize_overrides(overrides)
    if not clean:
        return base
    base_data = base.model_dump()

    # Switching the embedding provider must NOT inherit the previous provider's
    # model/dim — e.g. a hashing base (dim 384) must not size an OpenAI
    # collection. Drop them unless the override supplies its own.
    emb = clean.get("embedding")
    if isinstance(emb, dict) and "name" in emb and emb["name"] != base_data["embedding"]["name"]:
        if "model" not in emb:
            base_data["embedding"]["model"] = None
        if "dim" not in emb:
            base_data["embedding"]["dim"] = None

    merged = _deep_merge(base_data, clean)
    return config_from_dict(merged)
