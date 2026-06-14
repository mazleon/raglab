"""Memory Engineering Platform.

A first-class, pluggable memory subsystem alongside RAG. Ten memory types over
two storage tiers (SQLite source of truth + Qdrant semantic recall), with
formation, lifecycle, consolidation, and scope-based governance. Use
:class:`MemoryManager` as the single entrypoint.
"""

from raglab.memory.manager import MemoryManager  # noqa: F401
from raglab.memory.types import (  # noqa: F401
    MEMORY_TYPES,
    Episode,
    MemoryHit,
    MemoryQuery,
    MemoryRecord,
    MemoryScope,
    WorkflowState,
)
