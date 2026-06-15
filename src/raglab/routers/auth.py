"""Authentication endpoints: register, login, logout, me.

Login/registration return an HS256 token in the body; the web BFF stores it in an
HTTP-only cookie and replays it as a ``Bearer`` token on proxied calls. A cookie
is also set on the API response so direct API clients work too.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field

from raglab.accounts.auth import (
    User,
    authenticate,
    issue_token,
    register_user,
)
from raglab.server.deps import COOKIE_NAME, current_user

router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE_MAX_AGE = 60 * 60 * 24 * 7


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    name: str = ""
    tenant: str = "default"


class LoginRequest(BaseModel):
    email: str
    password: str


def _user_dict(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "tenant_id": user.tenant_id,
        "role": user.role,
    }


def _auth_response(response: Response, user: User) -> dict[str, Any]:
    token = issue_token(user)
    response.set_cookie(
        COOKIE_NAME, token, max_age=_COOKIE_MAX_AGE, httponly=True, samesite="lax"
    )
    return {"user": _user_dict(user), "token": token}


@router.post("/register")
def register(req: RegisterRequest, response: Response) -> dict[str, Any]:
    user = register_user(str(req.email), req.password, name=req.name, tenant=req.tenant)
    return _auth_response(response, user)


@router.post("/login")
def login(req: LoginRequest, response: Response) -> dict[str, Any]:
    user = authenticate(str(req.email), req.password)
    return _auth_response(response, user)


@router.post("/logout")
def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(current_user)) -> dict[str, Any]:
    return {"user": _user_dict(user)}
