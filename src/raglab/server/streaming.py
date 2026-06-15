"""Server-Sent Events generator for the chat experience.

Emits a stable, ordered event stream the browser renders incrementally:

    meta     once   — resolved architecture / model / embedding + conversation id
    trace    0..n   — one per pipeline TrajectoryStep (live reasoning timeline)
    delta    0..n   — answer text, chunked for a typewriter effect
    sources  once   — cited contexts
    metrics  once   — latency / tokens / cost / retries
    done     once   — terminal marker
    error    once   — terminal; replaces the above on failure

The blocking pipeline runs in a worker thread so the event loop keeps serving.
True token-level streaming isn't exposed by the LLM protocol yet; the wire format
is forward-compatible so a future native-streaming LLM needs no client change.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any

import anyio

from raglab.accounts.auth import User, user_to_scope
from raglab.core.types import RAGResult
from raglab.errors import RaglabError
from raglab.server.sessions import get_engine

logger = logging.getLogger("raglab.stream")

_TRACE_DELAY = 0.04
_DELTA_DELAY = 0.012
_DELTA_SIZE = 24


def sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


def _chunk(text: str, size: int = _DELTA_SIZE) -> Iterator[str]:
    for i in range(0, len(text), size):
        yield text[i : i + size]


def _contexts(result: RAGResult) -> list[dict[str, Any]]:
    return [
        {
            "score": round(sc.score, 4),
            "source": sc.chunk.metadata.get("source", sc.chunk.document_id),
            "text": sc.text,
        }
        for sc in result.contexts
    ]


def _metrics(result: RAGResult) -> dict[str, Any]:
    m = result.metrics
    return {
        "latency_ms": round(m.latency_ms, 1),
        "total_tokens": m.total_tokens,
        "prompt_tokens": m.prompt_tokens,
        "completion_tokens": m.completion_tokens,
        "usd_cost": m.usd_cost,
        "retries": m.retries,
        "retriever_hits": m.retriever_hits,
    }


def _record_episode(user: User, conversation_id: str, query: str, result: RAGResult) -> None:
    """Best-effort episodic memory write — never breaks the response."""

    try:
        from raglab.memory import Episode
        from raglab.server.state import get_memory

        scope = user_to_scope(user, session_id=conversation_id)
        get_memory().store("episodic").record_episode(
            Episode(
                goal=query,
                action=result.architecture,
                result=result.answer[:500],
                success=bool(result.answer.strip()),
            ),
            scope,
        )
    except Exception as exc:  # noqa: BLE001 - memory is auxiliary
        logger.debug("episodic memory write skipped: %s", exc)


async def chat_event_stream(
    *,
    user: User,
    query: str,
    cfg: Any,
    conversation_id: str,
    persist: bool = True,
) -> AsyncIterator[str]:
    yield sse(
        "meta",
        {
            "architecture": cfg.architecture,
            "model": cfg.llm.model or cfg.llm.provider,
            "provider": cfg.llm.provider,
            "embedding": cfg.embedding.name,
            "conversation_id": conversation_id,
        },
    )

    try:
        engine = get_engine(cfg)
        result: RAGResult = await anyio.to_thread.run_sync(engine.answer, query)
    except RaglabError as exc:
        yield sse("error", {"error": type(exc).__name__, "detail": str(exc)})
        return
    except Exception as exc:  # noqa: BLE001 - surface a clean error to the client
        logger.exception("chat stream failed")
        yield sse("error", {"error": "InternalError", "detail": str(exc)})
        return

    for step in result.trajectory:
        yield sse("trace", {"name": step.name, "detail": step.detail})
        await anyio.sleep(_TRACE_DELAY)

    for piece in _chunk(result.answer):
        yield sse("delta", {"text": piece})
        await anyio.sleep(_DELTA_DELAY)

    yield sse("sources", {"contexts": _contexts(result)})
    yield sse("metrics", _metrics(result))

    if persist and conversation_id:
        from raglab.accounts.conversations import append_message

        try:
            append_message(
                user, conversation_id, "assistant", result.answer,
                metadata={"sources": _contexts(result), "metrics": _metrics(result),
                          "architecture": result.architecture},
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("failed to persist assistant message: %s", exc)
        _record_episode(user, conversation_id, query, result)

    yield sse("done", {"conversation_id": conversation_id})
