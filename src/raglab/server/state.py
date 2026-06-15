"""Process-lifetime singletons shared by routers (memory manager)."""

from __future__ import annotations

import os
from typing import Any

_memory: Any = None


def get_memory() -> Any:
    """Process-lifetime MemoryManager. SQLite path + Qdrant location come from env
    (RAGLAB_MEMORY_DB / RAGLAB_MEMORY_QDRANT), defaulting to in-memory."""

    global _memory
    if _memory is None:
        from raglab.memory import MemoryManager

        _memory = MemoryManager(
            db_path=os.environ.get("RAGLAB_MEMORY_DB", ":memory:"),
            qdrant_location=os.environ.get("RAGLAB_MEMORY_QDRANT", ":memory:"),
        )
    return _memory
