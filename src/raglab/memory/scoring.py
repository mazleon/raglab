"""Memory scoring: importance, recency decay, and combined recall score.

Recall ranks memories by a weighted blend of semantic relevance, stored
importance, and recency, so a memory must be both relevant *and* salient/fresh to
surface. Lifecycle uses the same primitives to decay and prune.
"""

from __future__ import annotations

from datetime import datetime

from raglab.memory.types import now_dt

# relevance, importance, recency
DEFAULT_WEIGHTS = (0.6, 0.25, 0.15)


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def recency_score(timestamp_iso: str, half_life_hours: float = 72.0) -> float:
    """1.0 for just-now, halving every ``half_life_hours``. Range (0, 1]."""

    try:
        age_h = (now_dt() - _parse(timestamp_iso)).total_seconds() / 3600.0
    except (ValueError, TypeError):
        return 0.0
    age_h = max(age_h, 0.0)
    return float(0.5 ** (age_h / half_life_hours))


def importance_from_signals(
    content: str,
    *,
    base: float = 0.5,
    success: bool | None = None,
    has_feedback: bool = False,
    explicit: float | None = None,
) -> float:
    """Heuristic importance in [0, 1]. Failures and feedback are more salient
    (worth remembering); trivially short content is less important."""

    if explicit is not None:
        return max(0.0, min(1.0, explicit))
    score = base
    if len(content.strip()) < 20:
        score -= 0.15
    if has_feedback:
        score += 0.15
    if success is False:  # failures are valuable to remember
        score += 0.2
    elif success is True:
        score += 0.05
    return max(0.0, min(1.0, score))


def combined_score(
    relevance: float,
    importance: float,
    recency: float,
    weights: tuple[float, float, float] = DEFAULT_WEIGHTS,
) -> float:
    wr, wi, wc = weights
    return round(wr * relevance + wi * importance + wc * recency, 4)


def decayed_importance(
    importance: float, last_accessed_at_iso: str, rate_per_day: float = 0.02
) -> float:
    """Linearly decay importance with idle time, floored at 0."""

    try:
        idle_days = (now_dt() - _parse(last_accessed_at_iso)).total_seconds() / 86400.0
    except (ValueError, TypeError):
        return importance
    return max(0.0, round(importance - rate_per_day * max(idle_days, 0.0), 4))
