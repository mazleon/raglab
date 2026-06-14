"""Core data structures for the Memory Engineering Platform.

A :class:`MemoryRecord` is the universal unit of memory. SQLite is its source of
truth; records that need semantic recall are additionally embedded into Qdrant.
:class:`MemoryScope` provides multi-tenant isolation and governance.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def _now() -> str:
    return datetime.now(UTC).isoformat()


def now_dt() -> datetime:
    return datetime.now(UTC)


# Memory type identifiers (one registered store each).
MEMORY_TYPES = (
    "working",
    "episodic",
    "semantic",
    "procedural",
    "long_term",
    "reflection",
    "agent",
    "shared",
    "workflow",
    "graph",
)


@dataclass(frozen=True)
class MemoryScope:
    """Isolation + governance boundary. Empty fields act as wildcards on recall."""

    tenant_id: str = "default"
    user_id: str = "default"
    agent_id: str = ""
    session_id: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
        }


@dataclass
class MemoryRecord:
    content: str
    type: str = "semantic"
    scope: MemoryScope = field(default_factory=MemoryScope)
    importance: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)
    structured: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    last_accessed_at: str = field(default_factory=_now)
    access_count: int = 0
    expires_at: str | None = None  # ISO timestamp; None = no TTL
    embedded: bool = False  # whether a vector projection exists in Qdrant


@dataclass
class MemoryQuery:
    text: str = ""
    scope: MemoryScope = field(default_factory=MemoryScope)
    types: list[str] = field(default_factory=list)  # empty = all types
    k: int = 5
    min_importance: float = 0.0


@dataclass
class MemoryHit:
    record: MemoryRecord
    relevance: float = 0.0  # semantic similarity (0..1)
    score: float = 0.0  # combined relevance + importance + recency

    @property
    def content(self) -> str:
        return self.record.content


# ---- Type-specific structured payloads (stored in MemoryRecord.structured) ----
@dataclass
class Episode:
    goal: str
    action: str
    result: str
    feedback: str = ""
    success: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "action": self.action,
            "result": self.result,
            "feedback": self.feedback,
            "success": self.success,
        }

    def summary(self) -> str:
        status = "succeeded" if self.success else "failed"
        return f"Goal: {self.goal}\nAction: {self.action}\nResult ({status}): {self.result}"


@dataclass
class WorkflowState:
    goal: str
    subtasks: list[dict[str, Any]] = field(default_factory=list)  # {id, desc, status, agent}
    status: str = "running"  # running | completed | failed | paused
    current_step: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "subtasks": self.subtasks,
            "status": self.status,
            "current_step": self.current_step,
        }
