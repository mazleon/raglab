"""Built-in proxy metrics — LLM-free, deterministic, always available.

They approximate RAGAS-style metrics via token overlap so the leaderboard works
fully offline. When a judge LLM is configured, RAGAS (``ragas_eval``) and the LLM
judges (``llm_judges``) provide higher-fidelity scores.

A record is: {"question", "answer", "contexts": list[str], "ground_truth"}.
"""

from __future__ import annotations

import re
from collections.abc import Callable

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = {
    "the", "a", "an", "is", "are", "of", "to", "and", "in", "on", "for", "what",
    "does", "do", "how", "why", "which", "that", "this", "with", "as", "by", "it",
}


def _toks(text: str) -> set[str]:
    return {t for t in _TOKEN.findall((text or "").lower()) if t not in _STOP}


def _ctx_tokens(record: dict) -> set[str]:
    out: set[str] = set()
    for c in record.get("contexts", []):
        out |= _toks(c)
    return out


def answer_nonempty(record: dict) -> float:
    ans = (record.get("answer") or "").strip().lower()
    return 0.0 if (not ans or ans.startswith("i don't know")) else 1.0


def context_recall_proxy(record: dict) -> float:
    gt = _toks(record.get("ground_truth", ""))
    if not gt:
        return 0.0
    return round(len(gt & _ctx_tokens(record)) / len(gt), 3)


def answer_relevancy_proxy(record: dict) -> float:
    ans, gt = _toks(record.get("answer", "")), _toks(record.get("ground_truth", ""))
    if not ans or not gt:
        return 0.0
    inter = len(ans & gt)
    prec = inter / len(ans)
    rec = inter / len(gt)
    if prec + rec == 0:
        return 0.0
    return round(2 * prec * rec / (prec + rec), 3)


def faithfulness_proxy(record: dict) -> float:
    ans, ctx = _toks(record.get("answer", "")), _ctx_tokens(record)
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
        return {m: 0.0 for m in metric_names}
    for name in metric_names:
        fn = METRICS.get(name)
        if fn is None:
            continue
        out[name] = round(sum(fn(r) for r in records) / len(records), 4)
    return out
