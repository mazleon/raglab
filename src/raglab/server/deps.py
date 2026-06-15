"""FastAPI dependencies: resolve the authenticated user from the session cookie.

The cookie (or a ``Bearer`` token for API clients) carries the HS256 JWT minted at
login. ``current_user`` raises :class:`AuthError` (→ 401) when absent/invalid;
``optional_user`` returns ``None`` instead, for endpoints that work logged-out.
"""

from __future__ import annotations

from fastapi import Request

from raglab.accounts.auth import User, decode_token
from raglab.errors import AuthError

COOKIE_NAME = "raglab_session"


def _token_from(request: Request) -> str | None:
    # An explicit Authorization header is an intentional act and wins over an
    # ambient session cookie (which may belong to a different identity).
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return request.cookies.get(COOKIE_NAME)


def current_user(request: Request) -> User:
    token = _token_from(request)
    if not token:
        raise AuthError("authentication required")
    return decode_token(token)


def optional_user(request: Request) -> User | None:
    try:
        return current_user(request)
    except AuthError:
        return None
