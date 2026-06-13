"""Recursive + fixed + parent-child chunkers.

The recursive splitter mirrors LangChain's RecursiveCharacterTextSplitter idea
(split on the largest natural separator that keeps chunks under ``chunk_size``,
with character overlap) but is dependency-free and deterministic.
"""

from __future__ import annotations

from raglab.core.registry import register
from raglab.core.types import Chunk, Document

_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def _split(text: str, size: int, seps: list[str]) -> list[str]:
    if len(text) <= size:
        return [text] if text.strip() else []
    sep = next((s for s in seps if s and s in text), "")
    if sep == "":
        return [text[i : i + size] for i in range(0, len(text), size)]
    parts = text.split(sep)
    chunks: list[str] = []
    buf = ""
    for part in parts:
        piece = part + sep
        if len(buf) + len(piece) <= size:
            buf += piece
        else:
            if buf.strip():
                chunks.append(buf)
            if len(piece) > size:
                chunks.extend(_split(piece, size, seps[seps.index(sep) + 1 :]))
                buf = ""
            else:
                buf = piece
    if buf.strip():
        chunks.append(buf)
    return chunks


def _overlap(chunks: list[str], overlap: int) -> list[str]:
    if overlap <= 0 or len(chunks) <= 1:
        return chunks
    out = [chunks[0]]
    for prev, cur in zip(chunks, chunks[1:], strict=False):
        tail = prev[-overlap:]
        out.append(tail + cur)
    return out


def _emit(doc: Document, texts: list[str], extra: dict | None = None) -> list[Chunk]:
    chunks = []
    for i, t in enumerate(texts):
        meta = dict(doc.metadata)
        meta["chunk_index"] = i
        if extra:
            meta.update(extra)
        chunks.append(Chunk(text=t.strip(), metadata=meta, document_id=doc.document_id))
    return chunks


@register("chunker", "recursive")
class RecursiveChunker:
    def __init__(self, chunk_size: int = 800, overlap: int = 120, **_: object) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, docs: list[Document]) -> list[Chunk]:
        out: list[Chunk] = []
        for doc in docs:
            pieces = _overlap(_split(doc.text, self.chunk_size, _SEPARATORS), self.overlap)
            out.extend(_emit(doc, pieces))
        return out


@register("chunker", "fixed")
class FixedChunker:
    def __init__(self, chunk_size: int = 800, overlap: int = 120, **_: object) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, docs: list[Document]) -> list[Chunk]:
        out: list[Chunk] = []
        step = max(1, self.chunk_size - self.overlap)
        for doc in docs:
            t = doc.text
            pieces = [t[i : i + self.chunk_size] for i in range(0, len(t), step)]
            out.extend(_emit(doc, pieces))
        return out


@register("chunker", "parent_child")
class ParentChildChunker:
    """Large parent chunks split into smaller child chunks; children carry a
    ``parent_text`` reference so a pipeline can expand context after retrieval."""

    def __init__(
        self, chunk_size: int = 1600, child_size: int = 400, overlap: int = 80, **_: object
    ) -> None:
        self.parent_size = chunk_size
        self.child_size = child_size
        self.overlap = overlap

    def chunk(self, docs: list[Document]) -> list[Chunk]:
        out: list[Chunk] = []
        for doc in docs:
            parents = _split(doc.text, self.parent_size, _SEPARATORS)
            for p_idx, parent in enumerate(parents):
                children = _overlap(
                    _split(parent, self.child_size, _SEPARATORS), self.overlap
                )
                out.extend(
                    _emit(
                        doc,
                        children,
                        extra={"parent_index": p_idx, "parent_text": parent.strip()},
                    )
                )
        return out
