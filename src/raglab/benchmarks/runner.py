"""Benchmark matrix runner.

Expands the cartesian product of every ``matrix`` list, resolves each cell into
a full :class:`ExperimentConfig` (merged over ``base``), ingests the corpus into
that cell's store, runs the dataset questions, and aggregates quality + cost +
latency into a ranked leaderboard (CSV + HTML).
"""

from __future__ import annotations

import itertools
import json
import logging
import time
import uuid
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from raglab.core.config import build_llm, config_from_dict
from raglab.core.utils import deep_merge
from raglab.errors import RaglabError
from raglab.evaluation.builtin import evaluate_builtin
from raglab.evaluation.reports import write_csv, write_html
from raglab.llms.metered import MeteredLLM
from raglab.service import build_engine

logger = logging.getLogger("raglab.benchmark")


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
        cfg = deep_merge(base, cell)
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


def _evaluate(
    records: list[dict[str, Any]],
    eval_cfg: dict[str, Any],
    raw_cfg: dict[str, Any],
    builtin_metrics: list[str],
) -> tuple[dict[str, Any], float, int, list[str]]:
    """Run builtin metrics, optional RAGAS, and optional LLM judges.

    Each LLM-backed step is isolated: a failing judge/RAGAS records an error and
    is skipped rather than aborting the whole benchmark. Returns
    (metrics, judge_cost_usd, judge_tokens, errors).
    """

    metrics: dict[str, Any] = evaluate_builtin(records, builtin_metrics)
    errors: list[str] = []
    judge_cost = 0.0
    judge_tokens = 0

    if eval_cfg.get("ragas"):
        try:
            from raglab.evaluation.ragas_eval import RagasEvaluator

            metrics.update(RagasEvaluator().evaluate(records))
        except Exception as e:  # noqa: BLE001 - never abort the matrix on one evaluator
            msg = f"ragas: {type(e).__name__}: {e}"
            logger.warning(msg)
            errors.append(msg)

    judges = eval_cfg.get("judges", [])
    if judges:
        from raglab.evaluation.llm_judges import LLMJudge

        judge_raw = eval_cfg.get("judge_llm") or raw_cfg.get("llm", {})
        try:
            judge_cfg = config_from_dict({"llm": judge_raw}).llm
            metered = MeteredLLM(build_llm(judge_cfg))
        except RaglabError as e:
            errors.append(f"judge_llm: {e}")
            return metrics, judge_cost, judge_tokens, errors

        delay_s = float(eval_cfg.get("judge_delay_s", 0.0))
        for dimension in judges:
            try:
                metrics.update(LLMJudge(dimension, metered).evaluate(records, delay_s=delay_s))
            except RaglabError as e:
                msg = f"judge[{dimension}]: {e}"
                logger.warning(msg)
                errors.append(msg)
                metrics[f"judge_{dimension}"] = None
        judge_cost = round(metered.total_cost, 6)
        judge_tokens = metered.total_tokens

    return metrics, judge_cost, judge_tokens, errors


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
    n = max(len(dataset), 1)
    for raw_cfg in expand_matrix(bench):
        raw_cfg = deepcopy(raw_cfg)
        # Unique collection per cell only when we re-ingest into in-memory stores.
        if corpus is not None:
            raw_cfg["collection"] = f"{raw_cfg.get('collection', 'bench')}_{uuid.uuid4().hex[:8]}"

        base_row: dict[str, Any] = {
            "experiment_id": uuid.uuid4().hex[:12],
            **_summarize(raw_cfg),
            "n_questions": len(dataset),
        }
        try:
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

            metrics, judge_cost, judge_tokens, errors = _evaluate(
                records, eval_cfg, raw_cfg, builtin_metrics
            )
            row = {
                **base_row,
                **{k: (round(v, 4) if isinstance(v, int | float) else v)
                   for k, v in metrics.items()},
                "avg_latency_ms": round(total_latency / n, 2),
                "answer_cost_usd": round(total_cost, 6),
                "judge_cost_usd": judge_cost,
                "total_cost_usd": round(total_cost + judge_cost, 6),
                "avg_tokens": round(total_tokens / n, 1),
                "judge_tokens": judge_tokens,
                "error": "; ".join(errors) if errors else "",
                "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
            }
        except RaglabError as e:
            # A whole cell failed (e.g. provider auth/model error). Record it and
            # keep going so the rest of the matrix still produces results.
            logger.error("benchmark cell failed (%s): %s", base_row, e)
            row = {
                **base_row,
                "error": f"{type(e).__name__}: {e}",
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
