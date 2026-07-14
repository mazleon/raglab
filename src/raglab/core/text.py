"""Shared lexical text utilities (tokenizer + stopword set).

Single source for the token-overlap heuristics used by retrieval grading,
reasoning, and the built-in proxy metrics so they stay in lockstep.
"""

from __future__ import annotations

import re

_TOKEN = re.compile(r"[a-z0-9]+")
STOP_WORDS: frozenset[str] = frozenset(
    {
        "the", "a", "an", "is", "are", "of", "to", "and", "in", "on", "for",
        "what", "does", "do", "how", "why", "which", "that", "this", "with",
        "as", "by", "it",
    }
)


def content_tokens(text: str) -> set[str]:
    """Content (non-stopword) tokens of ``text``. None/empty → empty set."""
    return {t for t in _TOKEN.findall((text or "").lower()) if t not in STOP_WORDS}