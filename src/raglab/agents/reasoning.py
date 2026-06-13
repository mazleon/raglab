"""Reasoning helpers: complexity routing, query decomposition, gap analysis.

All have deterministic, offline heuristics so every architecture runs without an
LLM. Each also accepts an optional ``llm`` to upgrade the heuristic when a real
model is configured.
"""

from __future__ import annotations

import re

from raglab.agents.grading import _content_tokens
from raglab.core.interfaces import LLM
from raglab.core.types import ScoredChunk

_SUBQ_SPLIT = re.compile(r"\s+and\s+|\s*;\s*|\?\s*")


def classify_complexity(query: str, llm: LLM | None = None) -> str:
    """Return 'simple' | 'moderate' | 'complex'.

    Heuristic: short factual single-clause -> simple; multi-clause / comparative
    / multi-hop signals -> complex; otherwise moderate.
    """

    q = query.lower()
    tokens = _content_tokens(query)
    n_clauses = len([p for p in _SUBQ_SPLIT.split(query) if p.strip()])
    multi_hop_signals = any(
        w in q for w in ("compare", "difference", "both", "and then", "versus", " vs ")
    )
    if n_clauses >= 2 or multi_hop_signals or len(tokens) > 14:
        return "complex"
    if len(tokens) <= 5:
        return "simple"
    return "moderate"


def decompose(query: str, max_subs: int = 3, llm: LLM | None = None) -> list[str]:
    """Split a multi-part question into sub-questions (heuristic)."""

    parts = [p.strip() for p in _SUBQ_SPLIT.split(query) if len(p.strip()) > 3]
    if len(parts) <= 1:
        return [query]
    subs = []
    for p in parts[:max_subs]:
        subs.append(p if p.endswith("?") else p + "?")
    return subs


def identify_gaps(query: str, contexts: list[ScoredChunk], max_terms: int = 4) -> list[str]:
    """Query content terms not yet covered by retrieved context — used to expand
    the search in deep-search / multi-round retrieval."""

    q = _content_tokens(query)
    covered: set[str] = set()
    for sc in contexts:
        covered |= _content_tokens(sc.text)
    missing = [t for t in q if t not in covered]
    return missing[:max_terms]
