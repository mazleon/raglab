"""Conversation + message endpoints (all scoped to the authenticated user)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from raglab.accounts import conversations as conv
from raglab.accounts.auth import User
from raglab.server.deps import current_user

router = APIRouter(prefix="/conversations", tags=["conversations"])


class CreateConversation(BaseModel):
    title: str = "New chat"
    pipeline: str = "naive"


class RenameConversation(BaseModel):
    title: str


@router.get("")
def list_all(user: User = Depends(current_user)) -> dict[str, Any]:
    rows = conv.list_conversations(user)
    return {"conversations": [c.to_dict() for c in rows], "count": len(rows)}


@router.post("")
def create(req: CreateConversation, user: User = Depends(current_user)) -> dict[str, Any]:
    c = conv.create_conversation(user, title=req.title, pipeline=req.pipeline)
    return c.to_dict()


@router.get("/{conversation_id}")
def get(conversation_id: str, user: User = Depends(current_user)) -> dict[str, Any]:
    c = conv.get_conversation(user, conversation_id)
    messages = conv.list_messages(user, conversation_id)
    return {**c.to_dict(), "messages": [m.to_dict() for m in messages]}


@router.patch("/{conversation_id}")
def rename(
    conversation_id: str, req: RenameConversation, user: User = Depends(current_user)
) -> dict[str, Any]:
    return conv.rename_conversation(user, conversation_id, req.title).to_dict()


@router.delete("/{conversation_id}")
def delete(conversation_id: str, user: User = Depends(current_user)) -> dict[str, bool]:
    return {"deleted": conv.delete_conversation(user, conversation_id)}
