"""Answer critic + citation attachment."""

from __future__ import annotations

from dataclasses import dataclass

from raglab.agents.grading import _content_tokens
from raglab.core.types import ScoredChunk


@dataclass
class CritiqueResult:
    ok: bool
    reason: str


def critique_answer(
    query: str, answer: str, contexts: list[ScoredChunk]
) -> CritiqueResult:
    """Flag ungrounded or empty answers. Heuristic: the answer must be non-empty
    and share content tokens with the retrieved context (i.e. be grounded)."""

    if not answer.strip() or answer.strip().lower().startswith("i don't know"):
        return CritiqueResult(False, "empty or non-committal answer")
    ans = _content_tokens(answer)
    ctx = set()
    for sc in contexts:
        ctx |= _content_tokens(sc.text)
    if ans and not (ans & ctx):
        return CritiqueResult(False, "answer not grounded in context")
    return CritiqueResult(True, "answer grounded")


def attach_citations(answer: str, contexts: list[ScoredChunk]) -> tuple[str, list[str]]:
    sources: list[str] = []
    for sc in contexts:
        src = str(sc.chunk.metadata.get("source", sc.chunk.document_id))
        if src and src not in sources:
            sources.append(src)
    return answer, sources
