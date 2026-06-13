"""Entity + relationship extraction.

The default ``heuristic`` extractor is deterministic and offline: it pulls
capitalized phrases and acronyms as entities and treats entities co-occurring in
the same chunk as related. An ``llm`` extractor can be layered on later for
higher recall.
"""

from __future__ import annotations

import re
from itertools import combinations

# Capitalized words/phrases or ALL-CAPS acronyms (>=2 chars).
_ENTITY = re.compile(r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)*|[A-Z]{2,})\b")
# Words that start sentences but aren't entities.
_NOISE = {
    "The", "This", "That", "These", "Those", "It", "A", "An", "Every", "When",
    "If", "For", "RAGLab",  # too common in our corpus to be informative alone
}


def extract_entities(text: str, max_entities: int = 12) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for m in _ENTITY.finditer(text):
        ent = m.group(1).strip()
        if ent in _NOISE or len(ent) < 3:
            continue
        key = ent.lower()
        if key not in seen:
            seen.add(key)
            found.append(ent)
        if len(found) >= max_entities:
            break
    return found


def extract_relations(entities: list[str]) -> list[tuple[str, str]]:
    """Co-occurrence relations: every pair of entities in the same chunk."""

    return list(combinations(sorted(set(entities)), 2))
