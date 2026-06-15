"""Non-streaming query + benchmark + experiment endpoints.

``/query`` mirrors the CLI: run one architecture over a config and return the
answer, contexts, metrics, and trajectory. It now also accepts inline
``overrides`` so callers can swap the model/embedding/retriever without a YAML.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from raglab.core.config import load_config
from raglab.core.overrides import apply_overrides
from raglab.evaluation.reports import write_html
from raglab.experiments.store import DEFAULT_DB, list_experiments
from raglab.service import build_engine

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
def query(req: QueryRequest) -> QueryResponse:
    try:
        cfg = load_config(req.config)
    except FileNotFoundError as e:
        raise HTTPException(404, f"config not found: {req.config}") from e
    cfg = apply_overrides(cfg, req.overrides)
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
