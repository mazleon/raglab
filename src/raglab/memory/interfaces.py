"""Memory store contract.

Every memory type implements this Protocol. Business logic (the manager, the API,
the agentic loop) depends only on this — never on a concrete store — so any type
is pluggable and independently replaceable, including its storage backend.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from raglab.memory.types import MemoryQuery, MemoryRecord, MemoryScope


@runtime_checkable
class MemoryStore(Protocol):
    type: str
    semantic: bool  # whether this store maintains a vector projection

    def add(self, record: MemoryRecord) -> str: ...

    def get(self, memory_id: str) -> MemoryRecord | None: ...

    def search(self, query: MemoryQuery) -> list[MemoryRecord]: ...

    def update(self, memory_id: str, **changes: object) -> bool: ...

    def delete(self, memory_id: str) -> bool: ...

    def list(self, scope: MemoryScope, limit: int = 100) -> list[MemoryRecord]: ...

    def prune(self, scope: MemoryScope | None = None) -> int: ...
