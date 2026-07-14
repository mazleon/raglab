"""Query rewriter used when retrieval grading is below threshold."""

from __future__ import annotations


def rewrite_query(query: str, attempt: int) -> str:
    """Deterministic query expansion. Each retry broadens the phrasing.

    A real deployment would call an LLM here; the signature is identical so it
    can be swapped without touching the agentic graph.
    """

    base = query.strip().rstrip("?.")
    expansions = [
        f"{base} definition meaning explanation",
        f"{base} details how works overview key points",
    ]
    idx = min(attempt, len(expansions)) - 1
    return expansions[max(idx, 0)] if expansions else query
