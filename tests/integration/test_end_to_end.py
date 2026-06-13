"""End-to-end slice: ingest -> query across all three implemented architectures,
plus a tiny benchmark. Runs fully offline (hashing embedder + in-memory Qdrant +
echo LLM), so it needs no Docker and no API keys."""

import pytest

from raglab.benchmarks.runner import run_benchmark
from raglab.core.config import load_config
from raglab.service import build_engine

ARCHS = ["configs/naive.yaml", "configs/hybrid.yaml", "configs/agentic.yaml"]


@pytest.mark.integration
@pytest.mark.parametrize("config_path", ARCHS)
def test_ingest_then_query(config_path):
    cfg = load_config(config_path)
    engine = build_engine(cfg, ingest_path="examples/docs")
    result = engine.answer("How does Reciprocal Rank Fusion score documents?")

    assert result.answer.strip()
    assert result.contexts, "expected retrieved contexts"
    assert result.metrics.retriever_hits > 0
    assert result.trajectory
    # the relevant chunk mentions RRF / rank
    joined = " ".join(result.context_texts).lower()
    assert "rank" in joined


@pytest.mark.integration
def test_agentic_self_correction_records_trajectory():
    cfg = load_config("configs/agentic.yaml")
    engine = build_engine(cfg, ingest_path="examples/docs")
    result = engine.answer("What does the grader do in Agentic RAG?")
    names = [s.name for s in result.trajectory]
    assert "plan" in names and "grade" in names and "generate" in names


@pytest.mark.integration
def test_benchmark_matrix_produces_leaderboard(tmp_path):
    import yaml

    bench = yaml.safe_load(open("configs/benchmark.yaml"))
    bench["output_dir"] = str(tmp_path)
    cfg_path = tmp_path / "bench.yaml"
    cfg_path.write_text(yaml.safe_dump(bench))

    rows = run_benchmark(cfg_path)
    assert len(rows) == 4  # 2 architectures x 2 retrieval settings
    assert (tmp_path / "leaderboard-latest.csv").exists()
    assert (tmp_path / "leaderboard-latest.html").exists()
    for row in rows:
        assert "context_recall_proxy" in row
        assert row["n_questions"] == 5
