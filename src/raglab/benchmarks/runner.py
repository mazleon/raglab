"""Benchmark matrix runner.

Expands the cartesian product of every ``matrix`` list, resolves each cell into
a full :class:`ExperimentConfig` (merged over ``base``), ingests the corpus into
that cell's store, runs the dataset questions, and aggregates quality + cost +
latency into a ranked leaderboard (CSV + HTML).
"""

from __future__ import annotations

import itertools
import json
import time
import uuid
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from raglab.core.config import config_from_dict
from raglab.evaluation.builtin import evaluate_builtin
from raglab.evaluation.reports import write_csv, write_html
from raglab.service import build_engine


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = deepcopy(v)
    return out


def expand_matrix(bench: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a full config dict for every cell of the matrix."""

    base = bench.get("base", {})
    matrix = bench.get("matrix", {})
    collection = bench.get("collection", "raglab_bench")
    keys = list(matrix)
    combos = list(itertools.product(*(matrix[k] for k in keys))) if keys else [()]

    configs: list[dict[str, Any]] = []
    for combo in combos:
        cell = {keys[i]: combo[i] for i in range(len(keys))}
        cfg = _deep_merge(base, cell)
        cfg.setdefault("collection", collection)
        configs.append(cfg)
    return configs


def _load_dataset(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _summarize(cfg: dict[str, Any]) -> dict[str, str]:
    def name(section: Any, key: str) -> str:
        if isinstance(section, dict):
            return str(section.get(key, ""))
        return str(section)

    return {
        "architecture": str(cfg.get("architecture", "")),
        "embedding": name(cfg.get("embedding", {}), "name"),
        "retrieval": name(cfg.get("retrieval", {}), "type"),
        "reranker": name(cfg.get("reranker", {}), "name"),
        "llm": name(cfg.get("llm", {}), "provider"),
    }


def run_benchmark(bench_path: str | Path) -> list[dict[str, Any]]:
    bench = yaml.safe_load(Path(bench_path).read_text()) or {}
    corpus = bench.get("corpus", "examples/docs")
    dataset = _load_dataset(bench.get("dataset", "examples/qa/qa.jsonl"))
    output_dir = Path(bench.get("output_dir", "reports"))
    eval_cfg = bench.get("evaluation", {})
    builtin_metrics = eval_cfg.get(
        "builtin_metrics",
        ["context_recall_proxy", "answer_relevancy_proxy", "answer_nonempty"],
    )

    rows: list[dict[str, Any]] = []
    for raw_cfg in expand_matrix(bench):
        # Unique collection per cell so in-memory stores never collide.
        raw_cfg = deepcopy(raw_cfg)
        raw_cfg["collection"] = f"{raw_cfg.get('collection', 'bench')}_{uuid.uuid4().hex[:8]}"
        config = config_from_dict(raw_cfg)
        engine = build_engine(config, ingest_path=corpus)

        records: list[dict[str, Any]] = []
        total_cost = 0.0
        total_tokens = 0
        total_latency = 0.0
        for item in dataset:
            result = engine.answer(item["question"])
            records.append(
                {
                    "question": item["question"],
                    "answer": result.answer,
                    "contexts": result.context_texts,
                    "ground_truth": item.get("ground_truth", ""),
                }
            )
            total_cost += result.metrics.usd_cost
            total_tokens += result.metrics.total_tokens
            total_latency += result.metrics.latency_ms

        metrics = evaluate_builtin(records, builtin_metrics)
        if eval_cfg.get("ragas"):
            from raglab.evaluation.ragas_eval import RagasEvaluator

            metrics.update(RagasEvaluator().evaluate(records))

        n = max(len(dataset), 1)
        row = {
            "experiment_id": uuid.uuid4().hex[:12],
            **_summarize(raw_cfg),
            "n_questions": len(dataset),
            **{k: round(v, 4) for k, v in metrics.items()},
            "avg_latency_ms": round(total_latency / n, 2),
            "total_cost_usd": round(total_cost, 6),
            "avg_tokens": round(total_tokens / n, 1),
            "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        rows.append(row)

    # Rank by the first quality metric available.
    sort_key = next((m for m in builtin_metrics if m in (rows[0] if rows else {})), None)
    if sort_key:
        rows.sort(key=lambda r: r.get(sort_key, 0.0), reverse=True)

    stamp = time.strftime("%Y%m%d-%H%M%S")
    write_csv(rows, output_dir / f"leaderboard-{stamp}.csv")
    write_html(rows, output_dir / f"leaderboard-{stamp}.html")
    write_csv(rows, output_dir / "leaderboard-latest.csv")
    write_html(rows, output_dir / "leaderboard-latest.html")

    # Persist to the experiment store so runs accumulate across sessions.
    from raglab.experiments.store import save_experiments

    save_experiments(rows, str(output_dir / "experiments.db"))
    return rows
