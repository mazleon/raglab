"""Shared data structures that flow between every RAGLab component.

These are deliberately plain dataclasses with no provider coupling so that any
parser, embedder, retriever, reranker, LLM, or pipeline can produce and consume
them interchangeably.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

Vector = list[float]


@dataclass(slots=True)
class Document:
    """A parsed source document, before chunking."""

    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    document_id: str = field(default_factory=lambda: uuid.uuid4().hex)


@dataclass(slots=True)
class Chunk:
    """A retrievable unit of text with provenance metadata.

    Metadata conventionally carries: source, page, section, title, timestamp,
    author, document_id. ``chunk_id`` and ``document_id`` are first-class so the
    vector store and citation step can rely on them.
    """

    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    chunk_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    document_id: str = ""

    @property
    def source(self) -> str:
        return str(self.metadata.get("source", ""))


@dataclass(slots=True)
class ScoredChunk:
    """A chunk paired with a retrieval/rerank score."""

    chunk: Chunk
    score: float = 0.0

    @property
    def text(self) -> str:
        return self.chunk.text


@dataclass(slots=True)
class LLMResponse:
    """An LLM generation result that carries usage so cost can be computed."""

    text: str
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    usd_cost: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass(slots=True)
class RunMetrics:
    """Per-run measurements aggregated across every LLM/retrieval call."""

    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    usd_cost: float = 0.0
    retriever_hits: int = 0
    retries: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def add_llm(self, resp: LLMResponse) -> None:
        self.prompt_tokens += resp.prompt_tokens
        self.completion_tokens += resp.completion_tokens
        self.usd_cost += resp.usd_cost


@dataclass(slots=True)
class TrajectoryStep:
    """A single step in an (agentic) pipeline's reasoning trajectory."""

    name: str
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RAGResult:
    """The uniform output of every architecture's ``Pipeline.run``."""

    query: str
    answer: str
    contexts: list[ScoredChunk] = field(default_factory=list)
    trajectory: list[TrajectoryStep] = field(default_factory=list)
    metrics: RunMetrics = field(default_factory=RunMetrics)
    architecture: str = ""

    @property
    def context_texts(self) -> list[str]:
        return [c.text for c in self.contexts]


class _Timer:
    """Context manager that records elapsed wall-clock time into RunMetrics."""

    def __init__(self, metrics: RunMetrics) -> None:
        self.metrics = metrics
        self._start = 0.0

    def __enter__(self) -> _Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc: object) -> None:
        self.metrics.latency_ms += (time.perf_counter() - self._start) * 1000.0


def timer(metrics: RunMetrics) -> _Timer:
    return _Timer(metrics)
