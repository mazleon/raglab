"""Non-streaming query + benchmark + experiment endpoints.

``/query`` mirrors ``/chat`` and ``/documents``: it composes a **tenant-scoped**
engine through :mod:`raglab.server.sessions` (so the collection it queries is the
one a tenant's uploads land in) and requires an authenticated user. Inline
``overrides`` let callers swap model/embedding/retriever without a YAML.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from raglab.accounts.auth import User
from raglab.evaluation.reports import write_html
from raglab.experiments.catalog import DEFAULT_DB, list_experiments
from raglab.server.deps import current_user
from raglab.server.sessions import build_session_config, get_engine, ingest_file

router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    query: str
    config: str = "configs/pipelines/naive.yaml"
    ingest_path: str | None = None
    overrides: dict[str, Any] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    architecture: str
    answer: str
    contexts: list[dict[str, Any]]
    metrics: dict[str, Any]
    trajectory: list[str]


class BenchmarkRequest(BaseModel):
    config: str = "configs/benchmarks/offline.yaml"


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest, user: User = Depends(current_user)) -> QueryResponse:
    cfg = build_session_config(
        tenant_id=user.tenant_id,
        config_path=req.config,
        overrides=req.overrides,
    )
    engine = get_engine(cfg)
    if req.ingest_path:
        try:
            ingest_file(cfg, req.ingest_path)
        except FileNotFoundError as e:
            raise HTTPException(404, f"ingest path not found: {req.ingest_path}") from e
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


@router.post("/benchmark")
def benchmark(req: BenchmarkRequest) -> dict[str, Any]:
    from raglab.benchmarks.runner import run_benchmark

    rows = run_benchmark(req.config)
    return {"experiments": rows, "count": len(rows)}


@router.get("/experiments")
def experiments() -> dict[str, Any]:
    rows = list_experiments(DEFAULT_DB)
    return {"experiments": rows, "count": len(rows)}


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    import tempfile
    from pathlib import Path

    rows = list_experiments(DEFAULT_DB)
    if not rows:
        return "<h1>RAGLab</h1><p>No experiments yet. Run <code>raglab bench</code>.</p>"
    tmp = Path(tempfile.gettempdir()) / "raglab_dashboard.html"
    write_html(rows, tmp, title="RAGLab Experiment Dashboard")
    return tmp.read_text()