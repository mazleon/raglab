"""Backward-compat shim.

The reasoning primitives live in :mod:`raglab.reasoning` (``agents`` was a
misnomer — these are grading / critique / query-reasoning helpers, not
autonomous agents). This package re-exports the public names so existing
``from raglab.agents import ...`` calls keep working; new code should import
from :mod:`raglab.reasoning`.
"""

from raglab.reasoning import (  # noqa: F401
    CritiqueResult,
    GradeResult,
    attach_citations,
    classify_complexity,
    critique_answer,
    decompose,
    grade_retrieval,
    identify_gaps,
    rewrite_query,
)

__all__ = [
    "CritiqueResult",
    "GradeResult",
    "attach_citations",
    "classify_complexity",
    "critique_answer",
    "decompose",
    "grade_retrieval",
    "identify_gaps",
    "rewrite_query",
]