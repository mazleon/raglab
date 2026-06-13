"""Component contracts.

Every swappable part of RAGLab is defined here as a ``Protocol``. Business logic
(pipelines, benchmark runner, CLI, API) depends only on these protocols — never
on a concrete provider — which is what makes the platform plug-and-play.

Concrete implementations live in their own modules and register themselves with
``raglab.core.registry``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from raglab.core.types import (
    Chunk,
    Document,
    LLMResponse,
    RAGResult,
    ScoredChunk,
    Vector,
)


@runtime_checkable
class Parser(Protocol):
    """Turns a file on disk into one or more :class:`Document` objects."""

    def parse(self, path: Path) -> list[Document]: ...

    def supports(self, path: Path) -> bool: ...


@runtime_checkable
class Chunker(Protocol):
    """Splits documents into retrievable chunks."""

    def chunk(self, docs: list[Document]) -> list[Chunk]: ...


@runtime_checkable
class Embedder(Protocol):
    """Maps text to dense vectors."""

    @property
    def dim(self) -> int: ...

    def embed_documents(self, texts: list[str]) -> list[Vector]: ...

    def embed_query(self, text: str) -> Vector: ...


@runtime_checkable
class VectorStore(Protocol):
    """Stores chunk vectors and answers nearest-neighbour queries."""

    def ensure_collection(self, dim: int) -> None: ...

    def upsert(self, chunks: list[Chunk], vectors: list[Vector]) -> None: ...

    def search(
        self, vector: Vector, k: int, where: dict[str, Any] | None = None
    ) -> list[ScoredChunk]: ...

    def all_chunks(self) -> list[Chunk]: ...


@runtime_checkable
class Retriever(Protocol):
    """Returns scored chunks relevant to a query."""

    def retrieve(self, query: str, k: int) -> list[ScoredChunk]: ...


@runtime_checkable
class Reranker(Protocol):
    """Reorders candidate chunks for a query."""

    def rerank(
        self, query: str, chunks: list[ScoredChunk], top_n: int
    ) -> list[ScoredChunk]: ...


@runtime_checkable
class LLM(Protocol):
    """Chat/completion model that reports token usage and cost."""

    @property
    def model(self) -> str: ...

    def generate(
        self, messages: list[dict[str, str]], **kwargs: Any
    ) -> LLMResponse: ...


@runtime_checkable
class Pipeline(Protocol):
    """A complete RAG architecture. Every architecture conforms to this."""

    name: str

    def run(self, query: str) -> RAGResult: ...


@runtime_checkable
class Evaluator(Protocol):
    """Scores a batch of (question, answer, contexts, ground_truth) records."""

    def evaluate(self, records: list[dict[str, Any]]) -> dict[str, float]: ...
