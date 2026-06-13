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

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from raglab.core import registry
from raglab.core.config import load_config
from raglab.env import ensure_loaded
from raglab.evaluation.reports import write_html
from raglab.experiments.store import DEFAULT_DB, list_experiments
from raglab.service import build_engine

ensure_loaded()
app = FastAPI(title="RAGLab", version="0.1.0")


class QueryRequest(BaseModel):
    query: str
    config: str = "configs/naive.yaml"
    ingest_path: str | None = None


class QueryResponse(BaseModel):
    architecture: str
    answer: str
    contexts: list[dict[str, Any]]
    metrics: dict[str, Any]
    trajectory: list[str]


class BenchmarkRequest(BaseModel):
    config: str = "configs/benchmark.yaml"


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
