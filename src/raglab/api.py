"""FastAPI service exposing the same pipelines as the CLI.

    uvicorn raglab.api:app --reload

Endpoints:
    GET  /health
    GET  /architectures
    POST /query       {query, config, ingest_path?}
    POST /benchmark   {config}
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from raglab.core import registry
from raglab.core.config import load_config
from raglab.env import ensure_loaded
from raglab.errors import ConfigError, ProviderError, RaglabError
from raglab.evaluation.reports import write_html
from raglab.experiments.store import DEFAULT_DB, list_experiments
from raglab.service import build_engine

ensure_loaded()
app = FastAPI(title="RAGLab", version="0.1.0")


@app.exception_handler(RaglabError)
def _raglab_error_handler(_request: Request, exc: RaglabError) -> JSONResponse:
    # Config mistakes are the caller's fault (400); upstream provider failures
    # are a bad gateway (502).
    status = 400 if isinstance(exc, ConfigError) else 502 if isinstance(exc, ProviderError) else 500
    return JSONResponse(
        status_code=status,
        content={"error": type(exc).__name__, "detail": str(exc)},
    )


class QueryRequest(BaseModel):
    query: str
    config: str = "configs/pipelines/naive.yaml"
    ingest_path: str | None = None


class QueryResponse(BaseModel):
    architecture: str
    answer: str
    contexts: list[dict[str, Any]]
    metrics: dict[str, Any]
    trajectory: list[str]


class BenchmarkRequest(BaseModel):
    config: str = "configs/benchmarks/offline.yaml"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/architectures")
def architectures() -> dict[str, list[str]]:
    return {"architectures": registry.available("architecture")}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    try:
        cfg = load_config(req.config)
    except FileNotFoundError as e:
        raise HTTPException(404, f"config not found: {req.config}") from e
    engine = build_engine(cfg, ingest_path=req.ingest_path)
    result = engine.answer(req.query)
    return QueryResponse(
        architecture=result.architecture,
        answer=result.answer,
        contexts=[
            {
                "score": sc.score,
                "source": sc.chunk.metadata.get("source", ""),
                "text": sc.text,
            }
            for sc in result.contexts
        ],
        metrics={
            "latency_ms": result.metrics.latency_ms,
            "total_tokens": result.metrics.total_tokens,
            "usd_cost": result.metrics.usd_cost,
            "retries": result.metrics.retries,
            "retriever_hits": result.metrics.retriever_hits,
        },
        trajectory=[s.name for s in result.trajectory],
    )


@app.post("/benchmark")
def benchmark(req: BenchmarkRequest) -> dict[str, Any]:
    from raglab.benchmarks.runner import run_benchmark

    rows = run_benchmark(req.config)
    return {"experiments": rows, "count": len(rows)}


@app.get("/experiments")
def experiments() -> dict[str, Any]:
    rows = list_experiments(DEFAULT_DB)
    return {"experiments": rows, "count": len(rows)}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    import tempfile
    from pathlib import Path

    rows = list_experiments(DEFAULT_DB)
    if not rows:
        return "<h1>RAGLab</h1><p>No experiments yet. Run <code>raglab bench</code>.</p>"
    tmp = Path(tempfile.gettempdir()) / "raglab_dashboard.html"
    write_html(rows, tmp, title="RAGLab Experiment Dashboard")
    return tmp.read_text()


# --------------------------------------------------------------------------- #
# Memory Engineering Platform
# --------------------------------------------------------------------------- #
_memory: Any = None


def get_memory() -> Any:
    """Process-lifetime MemoryManager. SQLite path + Qdrant location come from
    env (RAGLAB_MEMORY_DB / RAGLAB_MEMORY_QDRANT), defaulting to in-memory."""

    global _memory
    if _memory is None:
        import os

        from raglab.memory import MemoryManager

        _memory = MemoryManager(
            db_path=os.environ.get("RAGLAB_MEMORY_DB", ":memory:"),
            qdrant_location=os.environ.get("RAGLAB_MEMORY_QDRANT", ":memory:"),
        )
    return _memory


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


@app.post("/memory/remember")
def memory_remember(req: RememberRequest) -> dict[str, Any]:
    mem = get_memory()
    mid = mem.remember(
        req.type, req.content, req.scope.to_scope(),
        importance=req.importance, structured=req.structured,
        metadata=req.metadata, ttl_seconds=req.ttl_seconds, force=req.force,
    )
    return {"id": mid, "stored": mid is not None}


@app.post("/memory/recall")
def memory_recall(req: RecallRequest) -> dict[str, Any]:
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


@app.get("/memory/timeline")
def memory_timeline(
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


@app.get("/memory/stats")
def memory_stats(tenant_id: str = "default", user_id: str = "default") -> dict[str, Any]:
    from raglab.memory import MemoryScope

    return get_memory().stats(MemoryScope(tenant_id=tenant_id, user_id=user_id))


@app.delete("/memory/{memory_id}")
def memory_forget(memory_id: str) -> dict[str, Any]:
    return {"deleted": get_memory().forget(memory_id)}


@app.post("/memory/erase")
def memory_erase(scope: ScopeModel) -> dict[str, Any]:
    """GDPR erase: delete every memory matching the scope."""

    return {"erased": get_memory().erase(scope.to_scope())}
