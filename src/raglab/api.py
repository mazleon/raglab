"""FastAPI service — the enterprise RAG chatbot backend.

Thin assembly layer: it wires middleware, a single domain-error handler, and the
per-concern routers (auth, chat, conversations, documents, config, query, memory).
All real logic lives in those routers + the ``raglab.server`` / ``raglab.accounts``
packages.

    uvicorn raglab.api:app --reload
"""

from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from raglab.accounts.db import init_db
from raglab.env import ensure_loaded
from raglab.errors import AuthError, ConfigError, ProviderError, RaglabError
from raglab.routers import auth, chat, config, conversations, documents, memory, query

ensure_loaded()
init_db()

app = FastAPI(title="RAGLab", version="1.0.0", description="Enterprise RAG chatbot API")

_origins = os.environ.get("RAGLAB_CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RaglabError)
def _raglab_error_handler(_request: Request, exc: RaglabError) -> JSONResponse:
    # Map each domain error to the right HTTP status.
    if isinstance(exc, AuthError):
        status = 401
    elif isinstance(exc, ConfigError):
        status = 400
    elif isinstance(exc, ProviderError):
        status = 502
    else:
        status = 500
    return JSONResponse(
        status_code=status,
        content={"error": type(exc).__name__, "detail": str(exc)},
    )


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


for _router in (
    auth.router,
    chat.router,
    conversations.router,
    documents.router,
    config.router,
    query.router,
    memory.router,
):
    app.include_router(_router)
