"""Accounts: users, tenants, auth, and persistent conversations (SQLite).

This is the application's source of truth for *who* is using RAGLab and *what*
they have said — distinct from the Memory Engineering Platform (semantic recall)
and the experiment store (benchmarks). Multi-tenant from the ground up: every row
is scoped by ``tenant_id`` so a user only ever sees their tenant's data, mirroring
the ``MemoryScope`` isolation used elsewhere.
"""

from raglab.accounts.auth import (
    AuthError,
    User,
    authenticate,
    decode_token,
    issue_token,
    register_user,
    user_to_scope,
)
from raglab.accounts.conversations import (
    Conversation,
    Message,
    append_message,
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    list_messages,
)
from raglab.accounts.db import init_db

__all__ = [
    "AuthError",
    "Conversation",
    "Message",
    "User",
    "append_message",
    "authenticate",
    "create_conversation",
    "decode_token",
    "delete_conversation",
    "get_conversation",
    "init_db",
    "issue_token",
    "list_conversations",
    "list_messages",
    "register_user",
    "user_to_scope",
]
