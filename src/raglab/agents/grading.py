"""Retrieval grader.

Scores whether retrieved context is relevant/complete enough to answer. The
default is a deterministic lexical-coverage heuristic so the agentic loop runs
offline; an LLM grader can be layered on by passing ``llm``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from raglab.core.types import ScoredChunk

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = {
    "the", "a", "an", "is", "are", "of", "to", "and", "in", "on", "for", "what",
    "does", "do", "how", "why", "which", "that", "this", "with", "as", "by", "it",
}


def _content_tokens(text: str) -> set[str]:
    return {t for t in _TOKEN.findall(text.lower()) if t not in _STOP}


@dataclass
class GradeResult:
    score: float
    reason: str


def grade_retrieval(query: str, contexts: list[ScoredChunk]) -> GradeResult:
    q = _content_tokens(query)
    if not q:
        return GradeResult(1.0, "empty query")
    if not contexts:
        return GradeResult(0.0, "no contexts retrieved")
    covered = set()
    for sc in contexts:
        covered |= _content_tokens(sc.text) & q
    coverage = len(covered) / len(q)
    reason = f"query-term coverage {len(covered)}/{len(q)}"
    return GradeResult(round(coverage, 3), reason)
