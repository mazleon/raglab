"""Registration, login, password hashing, and JWT issue/verify.

Deliberately dependency-light: passwords are hashed with stdlib ``hashlib.scrypt``
and sessions use a hand-rolled HS256 JWT (``hmac`` + ``hashlib``). No bcrypt,
no PyJWT. The token is what the web app stores in an HTTP-only cookie.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
import uuid
from dataclasses import dataclass
from datetime import UTC
from typing import Any

from raglab.accounts.db import connect
from raglab.errors import AuthError

logger = logging.getLogger("raglab.auth")

# scrypt work factors — interactive-login appropriate, ~tens of ms.
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_DKLEN = 32

_TOKEN_TTL = 60 * 60 * 24 * 7  # 7 days
_DEV_SECRET = "raglab-dev-secret-change-me"


def _secret() -> bytes:
    secret = os.environ.get("RAGLAB_JWT_SECRET")
    if not secret:
        logger.warning(
            "RAGLAB_JWT_SECRET is not set — using an insecure dev secret. "
            "Set RAGLAB_JWT_SECRET in production."
        )
        secret = _DEV_SECRET
    return secret.encode()


@dataclass(slots=True)
class User:
    id: str
    email: str
    name: str
    tenant_id: str
    role: str = "member"


# --------------------------------------------------------------------------- #
# Passwords
# --------------------------------------------------------------------------- #
def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Return ``(hash_hex, salt_hex)`` for ``password`` using scrypt."""

    salt_bytes = bytes.fromhex(salt) if salt else secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode(), salt=salt_bytes, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=_DKLEN
    )
    return digest.hex(), salt_bytes.hex()


def verify_password(password: str, hash_hex: str, salt_hex: str) -> bool:
    candidate, _ = hash_password(password, salt_hex)
    return hmac.compare_digest(candidate, hash_hex)


# --------------------------------------------------------------------------- #
# JWT (HS256, stdlib)
# --------------------------------------------------------------------------- #
def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def issue_token(user: User, ttl: int = _TOKEN_TTL) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "tenant_id": user.tenant_id,
        "role": user.role,
        "iat": now,
        "exp": now + ttl,
    }
    segments = [
        _b64url(json.dumps(header, separators=(",", ":")).encode()),
        _b64url(json.dumps(payload, separators=(",", ":")).encode()),
    ]
    signing_input = ".".join(segments).encode()
    sig = hmac.new(_secret(), signing_input, hashlib.sha256).digest()
    segments.append(_b64url(sig))
    return ".".join(segments)


def decode_token(token: str) -> User:
    """Verify signature + expiry and return the :class:`User`. Raises AuthError."""

    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError as exc:
        raise AuthError("malformed token") from exc

    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected = hmac.new(_secret(), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _b64url_decode(sig_b64)):
        raise AuthError("invalid token signature")

    payload: dict[str, Any] = json.loads(_b64url_decode(payload_b64))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise AuthError("token expired")
    return User(
        id=payload["sub"],
        email=payload["email"],
        name=payload.get("name", ""),
        tenant_id=payload["tenant_id"],
        role=payload.get("role", "member"),
    )


# --------------------------------------------------------------------------- #
# Registration / login
# --------------------------------------------------------------------------- #
def _now() -> str:
    from datetime import datetime

    return datetime.now(UTC).isoformat()


def _slug_tenant(name: str) -> str:
    base = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    return base or "default"


def register_user(
    email: str, password: str, name: str = "", tenant: str = "default"
) -> User:
    """Create a user (and tenant if new). Raises AuthError if email is taken."""

    email = email.strip().lower()
    if not email or "@" not in email:
        raise AuthError("a valid email is required")
    if len(password) < 8:
        raise AuthError("password must be at least 8 characters")

    tenant_id = _slug_tenant(tenant)
    hash_hex, salt_hex = hash_password(password)
    user = User(id=uuid.uuid4().hex, email=email, name=name or email.split("@")[0],
                tenant_id=tenant_id, role="owner")
    conn = connect()
    try:
        existing = conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise AuthError("an account with this email already exists")
        conn.execute(
            "INSERT OR IGNORE INTO tenants (id, name, created_at) VALUES (?,?,?)",
            (tenant_id, tenant, _now()),
        )
        conn.execute(
            "INSERT INTO users (id, email, password_hash, salt, name, tenant_id, role, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (user.id, user.email, hash_hex, salt_hex, user.name, user.tenant_id,
             user.role, _now()),
        )
        conn.commit()
        return user
    finally:
        conn.close()


def authenticate(email: str, password: str) -> User:
    """Verify credentials and return the user. Raises AuthError on failure."""

    email = email.strip().lower()
    conn = connect()
    try:
        row = conn.execute(
            "SELECT id, email, password_hash, salt, name, tenant_id, role "
            "FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    finally:
        conn.close()
    if row is None or not verify_password(password, row["password_hash"], row["salt"]):
        raise AuthError("invalid email or password")
    return User(id=row["id"], email=row["email"], name=row["name"],
                tenant_id=row["tenant_id"], role=row["role"])


def user_to_scope(user: User, session_id: str = "") -> Any:
    """Map an authenticated user to a MemoryScope for isolation."""

    from raglab.memory import MemoryScope

    return MemoryScope(tenant_id=user.tenant_id, user_id=user.id, session_id=session_id)
