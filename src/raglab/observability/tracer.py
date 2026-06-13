"""Pluggable tracing.

A ``Tracer`` opens named spans around pipeline work. Implementations: NoopTracer
(default), LangFuseTracer (self-hosted or cloud), and LangSmith (enabled via env
so LangChain/LangGraph auto-trace). Missing credentials degrade gracefully to
no-ops, so observability is opt-in and never breaks an offline run.
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Iterator
from typing import Any, Protocol, runtime_checkable

from raglab.core.config import ObservabilityCfg


@runtime_checkable
class Tracer(Protocol):
    @contextlib.contextmanager
    def span(self, name: str, **metadata: Any) -> Iterator[None]: ...

    def flush(self) -> None: ...


class NoopTracer:
    @contextlib.contextmanager
    def span(self, name: str, **metadata: Any) -> Iterator[None]:
        yield

    def flush(self) -> None:
        pass


class LangFuseTracer:
    def __init__(self) -> None:
        self._client = None
        try:
            from langfuse import Langfuse

            if os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get(
                "LANGFUSE_SECRET_KEY"
            ):
                self._client = Langfuse()
        except Exception:  # pragma: no cover - never break a run on telemetry
            self._client = None

    @contextlib.contextmanager
    def span(self, name: str, **metadata: Any) -> Iterator[None]:
        if self._client is None:
            yield
            return
        trace = None
        try:
            trace = self._client.trace(name=name, metadata=metadata)
        except Exception:  # pragma: no cover
            trace = None
        try:
            yield
        finally:
            with contextlib.suppress(Exception):
                if trace is not None:
                    trace.update(output={"completed": True})

    def flush(self) -> None:
        with contextlib.suppress(Exception):
            if self._client is not None:
                self._client.flush()


class CompositeTracer:
    def __init__(self, tracers: list[Tracer]) -> None:
        self._tracers = tracers

    @contextlib.contextmanager
    def span(self, name: str, **metadata: Any) -> Iterator[None]:
        with contextlib.ExitStack() as stack:
            for t in self._tracers:
                stack.enter_context(t.span(name, **metadata))
            yield

    def flush(self) -> None:
        for t in self._tracers:
            t.flush()


def build_tracer(cfg: ObservabilityCfg) -> Tracer:
    tracers: list[Tracer] = []
    if cfg.langsmith:
        # LangChain/LangGraph pick this up automatically from the environment.
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    if cfg.langfuse:
        tracers.append(LangFuseTracer())
    if not tracers:
        return NoopTracer()
    return CompositeTracer(tracers)
