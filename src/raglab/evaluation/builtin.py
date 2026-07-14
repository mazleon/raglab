"""Built-in proxy metrics — LLM-free, deterministic, always available.

They approximate RAGAS-style metrics via token overlap so the leaderboard works
fully offline. When a judge LLM is configured, RAGAS (``ragas_eval``) and the LLM
judges (``llm_judges``) provide higher-fidelity scores.

A record is: {"question", "answer", "contexts": list[str], "ground_truth"}.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from raglab.core.registry import register
from raglab.core.text import content_tokens


def _ctx_tokens(record: dict) -> set[str]:
    out: set[str] = set()
    for c in record.get("contexts", []):
        out |= content_tokens(c)
    return out


def answer_nonempty(record: dict) -> float:
    ans = (record.get("answer") or "").strip().lower()
    return 0.0 if (not ans or ans.startswith("i don't know")) else 1.0


def context_recall_proxy(record: dict) -> float:
    gt = content_tokens(record.get("ground_truth", ""))
    if not gt:
        return 0.0
    return round(len(gt & _ctx_tokens(record)) / len(gt), 3)


def answer_relevancy_proxy(record: dict) -> float:
    ans = content_tokens(record.get("answer", ""))
    gt = content_tokens(record.get("ground_truth", ""))
    if not ans or not gt:
        return 0.0
    inter = len(ans & gt)
    prec = inter / len(ans)
    rec = inter / len(gt)
    if prec + rec == 0:
        return 0.0
    return round(2 * prec * rec / (prec + rec), 3)


def faithfulness_proxy(record: dict) -> float:
    ans, ctx = content_tokens(record.get("answer", "")), _ctx_tokens(record)
    if not ans:
        return 0.0
    return round(len(ans & ctx) / len(ans), 3)


METRICS: dict[str, Callable[[dict], float]] = {
    "answer_nonempty": answer_nonempty,
    "context_recall_proxy": context_recall_proxy,
    "answer_relevancy_proxy": answer_relevancy_proxy,
    "faithfulness_proxy": faithfulness_proxy,
}


def evaluate_builtin(records: list[dict], metric_names: list[str]) -> dict[str, float]:
    """Mean of each requested metric across records."""

    out: dict[str, float] = {}
    if not records:
        return dict.fromkeys(metric_names, 0.0)
    for name in metric_names:
        fn = METRICS.get(name)
        if fn is None:
            continue
        out[name] = round(sum(fn(r) for r in records) / len(records), 4)
    return out


@register("evaluator", "builtin")
class BuiltinEvaluator:
    """Class form of the proxy metrics so every evaluator conforms to the
    :class:`raglab.core.interfaces.Evaluator` protocol and is reachable through
    the registry (``registry.create("evaluator", "builtin", ...)``)."""

    def __init__(self, metric_names: list[str] | None = None) -> None:
        self.metric_names = list(metric_names or METRICS.keys())

    def evaluate(self, records: list[dict[str, Any]]) -> dict[str, float]:
        return evaluate_builtin(records, self.metric_names)