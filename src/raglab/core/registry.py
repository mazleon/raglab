"""The dependency-injection mechanism.

Components register themselves with ``@register(kind, name)``; the config layer
builds them by name with ``create(kind, name, **kwargs)``. Nothing else in the
codebase imports a concrete implementation directly.

Implementation modules lazy-import their heavy/optional provider libraries
*inside* ``__init__``/methods, so importing the package (and registering the
class) never requires torch, openai, etc. to be installed.
"""

from __future__ import annotations

import importlib
from collections import defaultdict
from typing import Any, TypeVar

T = TypeVar("T")

# kind -> name -> class
_REGISTRY: dict[str, dict[str, type]] = defaultdict(dict)

# Implementation packages whose import triggers @register side effects.
_IMPL_PACKAGES = (
    "raglab.ingestion.parsers",
    "raglab.ingestion.chunkers",
    "raglab.embeddings",
    "raglab.vectorstores",
    "raglab.retrievers",
    "raglab.rerankers",
    "raglab.llms",
    "raglab.pipelines",
    "raglab.evaluation",
    "raglab.observability",
    "raglab.graph",
)

_bootstrapped = False


def register(kind: str, name: str):
    """Class decorator that records ``cls`` under ``(kind, name)``."""

    def decorator(cls: type[T]) -> type[T]:
        if name in _REGISTRY[kind]:
            existing = _REGISTRY[kind][name]
            if existing is not cls:
                raise ValueError(
                    f"Duplicate registration for {kind!r}/{name!r}: "
                    f"{existing!r} vs {cls!r}"
                )
        _REGISTRY[kind][name] = cls
        return cls

    return decorator


def bootstrap() -> None:
    """Import every implementation package so registrations run. Idempotent."""

    global _bootstrapped
    if _bootstrapped:
        return
    for pkg in _IMPL_PACKAGES:
        importlib.import_module(pkg)
    _bootstrapped = True


def available(kind: str) -> list[str]:
    bootstrap()
    return sorted(_REGISTRY[kind])


def get(kind: str, name: str) -> type:
    bootstrap()
    try:
        return _REGISTRY[kind][name]
    except KeyError:
        opts = ", ".join(available(kind)) or "<none>"
        raise KeyError(
            f"No {kind!r} registered as {name!r}. Available: {opts}"
        ) from None


def create(kind: str, name: str, **kwargs: Any) -> Any:
    """Instantiate a registered component."""

    return get(kind, name)(**kwargs)
