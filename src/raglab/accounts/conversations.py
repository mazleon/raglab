"""Persistent conversations + messages, always scoped by tenant + user.

Every read/write takes the owning ``User`` so a caller can never touch another
tenant's or user's conversation — the WHERE clause enforces isolation at the SQL
layer, not just in application code.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from raglab.accounts.auth import User
from raglab.accounts.db import connect
from raglab.errors import AuthError


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(slots=True)
class Message:
    id: str
    conversation_id: str
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class Conversation:
    id: str
    user_id: str
    tenant_id: str
    title: str
    pipeline: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "pipeline": self.pipeline,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def create_conversation(
    user: User, title: str = "New chat", pipeline: str = "naive"
) -> Conversation:
    conv = Conversation(
        id=uuid.uuid4().hex, user_id=user.id, tenant_id=user.tenant_id,
        title=title or "New chat", pipeline=pipeline, created_at=_now(), updated_at=_now(),
    )
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO conversations "
            "(id, user_id, tenant_id, title, pipeline, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (conv.id, conv.user_id, conv.tenant_id, conv.title, conv.pipeline,
             conv.created_at, conv.updated_at),
        )
        conn.commit()
        return conv
    finally:
        conn.close()


def list_conversations(user: User, limit: int = 100) -> list[Conversation]:
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT * FROM conversations WHERE tenant_id = ? AND user_id = ? "
            "ORDER BY updated_at DESC LIMIT ?",
            (user.tenant_id, user.id, limit),
        ).fetchall()
        return [_row_to_conv(r) for r in rows]
    finally:
        conn.close()


def get_conversation(user: User, conversation_id: str) -> Conversation:
    conn = connect()
    try:
        row = conn.execute(
            "SELECT * FROM conversations WHERE id = ? AND tenant_id = ? AND user_id = ?",
            (conversation_id, user.tenant_id, user.id),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise AuthError("conversation not found")
    return _row_to_conv(row)


def delete_conversation(user: User, conversation_id: str) -> bool:
    conn = connect()
    try:
        # Ownership check first so we never delete another user's messages.
        owned = conn.execute(
            "SELECT 1 FROM conversations WHERE id = ? AND tenant_id = ? AND user_id = ?",
            (conversation_id, user.tenant_id, user.id),
        ).fetchone()
        if owned is None:
            return False
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def append_message(
    user: User,
    conversation_id: str,
    role: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> Message:
    """Append a message after verifying the user owns the conversation."""

    get_conversation(user, conversation_id)  # raises if not owned
    msg = Message(
        id=uuid.uuid4().hex, conversation_id=conversation_id, role=role,
        content=content, metadata=metadata or {}, created_at=_now(),
    )
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, metadata_json, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (msg.id, msg.conversation_id, msg.role, msg.content,
             json.dumps(msg.metadata), msg.created_at),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (msg.created_at, conversation_id),
        )
        conn.commit()
        return msg
    finally:
        conn.close()


def rename_conversation(user: User, conversation_id: str, title: str) -> Conversation:
    get_conversation(user, conversation_id)
    conn = connect()
    try:
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, _now(), conversation_id),
        )
        conn.commit()
    finally:
        conn.close()
    return get_conversation(user, conversation_id)


def list_messages(user: User, conversation_id: str, limit: int = 500) -> list[Message]:
    get_conversation(user, conversation_id)  # ownership check
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ?",
            (conversation_id, limit),
        ).fetchall()
        return [_row_to_msg(r) for r in rows]
    finally:
        conn.close()


def _row_to_conv(r: Any) -> Conversation:
    return Conversation(
        id=r["id"], user_id=r["user_id"], tenant_id=r["tenant_id"], title=r["title"],
        pipeline=r["pipeline"], created_at=r["created_at"], updated_at=r["updated_at"],
    )


def _row_to_msg(r: Any) -> Message:
    return Message(
        id=r["id"], conversation_id=r["conversation_id"], role=r["role"],
        content=r["content"], metadata=json.loads(r["metadata_json"] or "{}"),
        created_at=r["created_at"],
    )
