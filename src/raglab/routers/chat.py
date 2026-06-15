"""Streaming chat endpoint — the heart of the app.

Resolves (or creates) the conversation, persists the user turn, composes a
tenant-scoped engine from the caller's pipeline/model choices, and streams the
answer back as SSE. The assistant turn + episodic memory are persisted as the
stream finishes (see :mod:`raglab.server.streaming`).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from raglab.accounts import conversations as conv
from raglab.accounts.auth import User
from raglab.server.deps import current_user
from raglab.server.sessions import build_session_config
from raglab.server.streaming import chat_event_stream

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    conversation_id: str | None = None
    pipeline: str | None = None
    config: str | None = None
    overrides: dict[str, Any] = Field(default_factory=dict)


def _resolve_conversation(user: User, req: ChatRequest) -> str:
    if req.conversation_id:
        conv.get_conversation(user, req.conversation_id)  # ownership check (raises)
        return req.conversation_id
    title = req.query.strip()[:60] or "New chat"
    return conv.create_conversation(user, title=title, pipeline=req.pipeline or "naive").id


@router.post("/stream")
def stream(req: ChatRequest, user: User = Depends(current_user)) -> StreamingResponse:
    conversation_id = _resolve_conversation(user, req)
    conv.append_message(user, conversation_id, "user", req.query)

    cfg = build_session_config(
        tenant_id=user.tenant_id,
        pipeline=req.pipeline,
        config_path=req.config,
        overrides=req.overrides,
    )
    generator = chat_event_stream(
        user=user, query=req.query, cfg=cfg, conversation_id=conversation_id
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
