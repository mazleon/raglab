"""Ingestion flow: Documents -> Parser -> Cleaner -> Chunker -> Enrich -> Embed -> Qdrant."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from raglab.core.config import (
    ExperimentConfig,
    build_chunker,
    build_embedder,
    build_vectorstore,
)
from raglab.core.interfaces import Chunker, Embedder, VectorStore
from raglab.core.types import Chunk
from raglab.ingestion.cleaners import clean_documents
from raglab.ingestion.enrich import enrich
from raglab.ingestion.parsers import parse_path

_SUPPORTED = {".txt", ".md", ".markdown", ".rst", ".log", ".html", ".htm",
              ".csv", ".tsv", ".pdf", ".docx"}


@dataclass
class IngestResult:
    files: int
    documents: int
    chunks: int


class IngestionPipeline:
    def __init__(
        self, chunker: Chunker, embedder: Embedder, store: VectorStore
    ) -> None:
        self.chunker = chunker
        self.embedder = embedder
        self.store = store

    @classmethod
    def from_config(cls, config: ExperimentConfig) -> IngestionPipeline:
        embedder = build_embedder(config.embedding)
        store = build_vectorstore(config.vectorstore, config.collection, embedder.dim)
        chunker = build_chunker(config.chunker)
        return cls(chunker, embedder, store)

    def _iter_files(self, path: Path):
        if path.is_file():
            yield path
            return
        for p in sorted(path.rglob("*")):
            if p.is_file() and p.suffix.lower() in _SUPPORTED:
                yield p

    def ingest(self, path: str | Path) -> IngestResult:
        root = Path(path)
        files = list(self._iter_files(root))
        documents = []
        for f in files:
            documents.extend(parse_path(f))
        documents = clean_documents(documents)

        chunks: list[Chunk] = enrich(self.chunker.chunk(documents))
        if chunks:
            vectors = self.embedder.embed_documents([c.text for c in chunks])
            self.store.upsert(chunks, vectors)
        return IngestResult(len(files), len(documents), len(chunks))
