"""Reusable building blocks shared by the Phase 3 architectures.

Keeping retrieve/rerank/generate/parent-expansion here means each architecture
file expresses only its *distinctive* control flow, not boilerplate.
"""

from __future__ import annotations

from raglab.core.config import Components
from raglab.core.types import Chunk, LLMResponse, RunMetrics, ScoredChunk
from raglab.pipelines.base import build_messages


def retrieve(components: Components, query: str, k: int) -> list[ScoredChunk]:
    return components.retriever.retrieve(query, k)


def rerank(
    components: Components, query: str, candidates: list[ScoredChunk], top_n: int
) -> list[ScoredChunk]:
    return components.reranker.rerank(query, candidates, top_n)


def generate(
    components: Components, query: str, contexts: list[ScoredChunk], metrics: RunMetrics
) -> LLMResponse:
    resp = components.llm.generate(build_messages(query, contexts))
    metrics.add_llm(resp)
    return resp


def generate_with_instruction(
    components: Components,
    query: str,
    contexts: list[ScoredChunk],
    instruction: str,
    metrics: RunMetrics,
) -> LLMResponse:
    """Generation with an extra steering instruction (used by reflective/CRAG)."""

    messages = build_messages(query, contexts)
    messages[0]["content"] += "\n" + instruction
    resp = components.llm.generate(messages)
    metrics.add_llm(resp)
    return resp


def expand_parents(contexts: list[ScoredChunk]) -> list[ScoredChunk]:
    """Replace child chunks with their parent text when parent-child chunking was
    used, so the LLM sees fuller context. No-op otherwise."""

    out: list[ScoredChunk] = []
    seen_parents: set[str] = set()
    for sc in contexts:
        parent = sc.chunk.metadata.get("parent_text")
        if parent:
            key = f"{sc.chunk.document_id}:{sc.chunk.metadata.get('parent_index')}"
            if key in seen_parents:
                continue
            seen_parents.add(key)
            out.append(
                ScoredChunk(
                    Chunk(
                        text=parent,
                        metadata=sc.chunk.metadata,
                        chunk_id=sc.chunk.chunk_id,
                        document_id=sc.chunk.document_id,
                    ),
                    sc.score,
                )
            )
        else:
            out.append(sc)
    return out


def dedup(contexts: list[ScoredChunk]) -> list[ScoredChunk]:
    seen: dict[str, ScoredChunk] = {}
    for sc in contexts:
        seen.setdefault(sc.chunk.chunk_id or sc.chunk.text, sc)
    return list(seen.values())
