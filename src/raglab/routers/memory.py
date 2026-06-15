"""Memory Engineering Platform endpoints (remember / recall / timeline / erase)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from raglab.server.state import get_memory

router = APIRouter(prefix="/memory", tags=["memory"])


class ScopeModel(BaseModel):
    tenant_id: str = "default"
    user_id: str = "default"
    agent_id: str = ""
    session_id: str = ""

    def to_scope(self) -> Any:
        from raglab.memory import MemoryScope

        return MemoryScope(**self.model_dump())


class RememberRequest(BaseModel):
    type: str
    content: str
    scope: ScopeModel = ScopeModel()
    importance: float | None = None
    structured: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    ttl_seconds: int | None = None
    force: bool = False


class RecallRequest(BaseModel):
    query: str
    scope: ScopeModel = ScopeModel()
    types: list[str] | None = None
    k: int = 5
    min_importance: float = 0.0


@router.post("/remember")
def remember(req: RememberRequest) -> dict[str, Any]:
    mem = get_memory()
    mid = mem.remember(
        req.type, req.content, req.scope.to_scope(),
        importance=req.importance, structured=req.structured,
        metadata=req.metadata, ttl_seconds=req.ttl_seconds, force=req.force,
    )
    return {"id": mid, "stored": mid is not None}


@router.post("/recall")
def recall(req: RecallRequest) -> dict[str, Any]:
    from raglab.memory import MemoryQuery

    mem = get_memory()
    q = MemoryQuery(
        text=req.query, scope=req.scope.to_scope(), k=req.k,
        min_importance=req.min_importance, types=req.types or [],
    )
    hits = mem.recall(q, types=req.types)
    return {
        "hits": [
            {
                "id": h.record.id, "type": h.record.type, "content": h.content,
                "relevance": round(h.relevance, 4), "score": h.score,
                "importance": h.record.importance,
            }
            for h in hits
        ],
        "count": len(hits),
    }


@router.get("/timeline")
def timeline(
    tenant_id: str = "default", user_id: str = "default", limit: int = 100
) -> dict[str, Any]:
    from raglab.memory import MemoryScope

    mem = get_memory()
    records = mem.timeline(MemoryScope(tenant_id=tenant_id, user_id=user_id), limit=limit)
    return {
        "timeline": [
            {"id": r.id, "type": r.type, "content": r.content[:160],
             "importance": r.importance, "created_at": r.created_at}
            for r in records
        ],
        "count": len(records),
    }


@router.get("/stats")
def stats(tenant_id: str = "default", user_id: str = "default") -> dict[str, Any]:
    from raglab.memory import MemoryScope

    return get_memory().stats(MemoryScope(tenant_id=tenant_id, user_id=user_id))


@router.delete("/{memory_id}")
def forget(memory_id: str) -> dict[str, Any]:
    return {"deleted": get_memory().forget(memory_id)}


@router.post("/erase")
def erase(scope: ScopeModel) -> dict[str, Any]:
    """GDPR erase: delete every memory matching the scope."""

    return {"erased": get_memory().erase(scope.to_scope())}
