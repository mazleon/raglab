"""Retrieval grader.

Scores whether retrieved context is relevant/complete enough to answer. The
default is a deterministic lexical-coverage heuristic so the agentic loop runs
offline; an LLM grader can be layered on by passing ``llm``.
"""

from __future__ import annotations

from dataclasses import dataclass

from raglab.core.text import content_tokens
from raglab.core.types import ScoredChunk


@dataclass
class GradeResult:
    score: float
    reason: str


def grade_retrieval(query: str, contexts: list[ScoredChunk]) -> GradeResult:
    q = content_tokens(query)
    if not q:
        return GradeResult(1.0, "empty query")
    if not contexts:
        return GradeResult(0.0, "no contexts retrieved")
    covered = set()
    for sc in contexts:
        covered |= content_tokens(sc.text) & q
    coverage = len(covered) / len(q)
    reason = f"query-term coverage {len(covered)}/{len(q)}"
    return GradeResult(round(coverage, 3), reason)