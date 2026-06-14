"""End-to-end slice: ingest -> query across every architecture, plus a tiny
benchmark. Runs fully offline (hashing embedder + in-memory Qdrant + echo LLM),
so it needs no Docker and no API keys.

The tests use a hermetic in-repo corpus written to ``tmp_path`` rather than the
mutable ``examples/docs`` directory, so they stay deterministic regardless of
what example documents are present.
"""

from pathlib import Path

import pytest

from raglab.benchmarks.runner import run_benchmark
from raglab.core.config import load_config
from raglab.service import build_engine

ARCHS = [
    "configs/pipelines/naive.yaml",
    "configs/pipelines/hybrid.yaml",
    "configs/pipelines/agentic.yaml",
]

_DOC = """# Retrieval Fundamentals

Hybrid retrieval combines dense vector search with sparse BM25 keyword search.
The two result lists are merged with Reciprocal Rank Fusion (RRF), which scores
each document by the sum of 1 / (k + rank) across the lists it appears in.

## Agentic RAG

A grader scores whether the retrieved context is relevant and complete, and a
low score triggers a query rewrite and a retry before generation.
"""


@pytest.fixture
def corpus(tmp_path):
    d = tmp_path / "corpus"
    d.mkdir()
    (d / "retrieval.md").write_text(_DOC)
    return str(d)


@pytest.mark.integration
@pytest.mark.parametrize("config_path", ARCHS)
def test_ingest_then_query(config_path, corpus):
    cfg = load_config(config_path)
    engine = build_engine(cfg, ingest_path=corpus)
    result = engine.answer("How does Reciprocal Rank Fusion score documents?")

    assert result.answer.strip()
    assert result.contexts, "expected retrieved contexts"
    assert result.metrics.retriever_hits > 0
    assert result.trajectory
    # the relevant chunk mentions RRF / rank
    joined = " ".join(result.context_texts).lower()
    assert "rank" in joined


@pytest.mark.integration
def test_all_architectures_run_offline(corpus):
    """Every registered architecture answers end-to-end on the in-memory store."""

    from raglab.core import registry

    base = load_config("configs/pipelines/hybrid.yaml")
    archs = registry.available("architecture")
    assert len(archs) >= 13
    for arch in archs:
        cfg = base.model_copy(deep=True)
        cfg.architecture = arch
        engine = build_engine(cfg, ingest_path=corpus)
        result = engine.answer("How does Reciprocal Rank Fusion score documents?")
        assert result.answer.strip(), f"{arch} produced empty answer"
        assert result.trajectory, f"{arch} produced no trajectory"
        assert result.architecture == arch


@pytest.mark.integration
def test_agentic_self_correction_records_trajectory(corpus):
    cfg = load_config("configs/pipelines/agentic.yaml")
    engine = build_engine(cfg, ingest_path=corpus)
    result = engine.answer("What does the grader do in Agentic RAG?")
    names = [s.name for s in result.trajectory]
    assert "plan" in names and "grade" in names and "generate" in names


@pytest.mark.integration
def test_benchmark_matrix_produces_leaderboard(tmp_path, corpus):
    import yaml

    bench = yaml.safe_load(Path("configs/benchmarks/offline.yaml").read_text())
    bench["output_dir"] = str(tmp_path)
    bench["corpus"] = corpus  # hermetic corpus, not examples/docs
    cfg_path = tmp_path / "bench.yaml"
    cfg_path.write_text(yaml.safe_dump(bench))

    rows = run_benchmark(cfg_path)
    assert len(rows) == 4  # 2 architectures x 2 retrieval settings
    assert (tmp_path / "leaderboard-latest.csv").exists()
    assert (tmp_path / "leaderboard-latest.html").exists()
    for row in rows:
        assert "context_recall_proxy" in row
        assert row["n_questions"] == 5
        assert row["error"] == ""  # offline matrix should never error
