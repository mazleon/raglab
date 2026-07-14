"""Small shared helpers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``patch`` into a deep copy of ``base`` (patch wins).

    Dict values are merged recursively; everything else is deep-copied so the
    result never aliases ``base`` or ``patch`` (callers reuse ``base`` across
    many patches, e.g. matrix cells). Callers that must drop ``None`` leaves
    (e.g. client overrides) sanitize the patch before calling.
    """
    out = deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = deepcopy(value)
    return out