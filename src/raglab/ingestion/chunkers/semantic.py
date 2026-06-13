"""Semantic + agentic chunkers (Phase 4).

SemanticChunker starts a new chunk when a sentence's embedding diverges from the
running chunk centroid (semantic boundary). It uses a configurable embedder
(``hashing`` by default, so it runs offline; lexical similarity stands in for
semantic similarity until a real embedder is configured).

AgenticChunker groups consecutive sentences into coherent "propositions" by
topic continuity — a deterministic heuristic stand-in for an LLM grouper.
"""

from __future__ import annotations

import re

import numpy as np

from raglab.core.registry import create, register
from raglab.core.types import Chunk, Document

_SENT = re.compile(r"(?<=[.!?])\s+")
_TOKEN = re.compile(r"[a-z0-9]+")


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT.split(text) if s.strip()]


def _emit(doc: Document, groups: list[list[str]], extra_key: str) -> list[Chunk]:
    chunks = []
    for i, group in enumerate(groups):
        text = " ".join(group).strip()
        if not text:
            continue
        meta = dict(doc.metadata)
        meta["chunk_index"] = i
        meta[extra_key] = True
        chunks.append(Chunk(text=text, metadata=meta, document_id=doc.document_id))
    return chunks


@register("chunker", "semantic")
class SemanticChunker:
    def __init__(
        self,
        chunk_size: int = 800,
        overlap: int = 0,
        threshold: float = 0.55,
        embedder_name: str = "hashing",
        **_: object,
    ) -> None:
        self.max_chars = chunk_size
        self.threshold = threshold
        self.embedder = create("embedder", embedder_name, dim=256)

    def _split_doc(self, doc: Document) -> list[list[str]]:
        sents = _sentences(doc.text)
        if len(sents) <= 1:
            return [sents] if sents else []
        vecs = [np.asarray(v, dtype=np.float32) for v in self.embedder.embed_documents(sents)]
        groups: list[list[str]] = [[sents[0]]]
        centroid = vecs[0].copy()
        size = len(sents[0])
        for sent, vec in zip(sents[1:], vecs[1:], strict=True):
            denom = (np.linalg.norm(centroid) * np.linalg.norm(vec)) or 1.0
            sim = float(centroid @ vec) / denom
            if sim < self.threshold or size + len(sent) > self.max_chars:
                groups.append([sent])
                centroid = vec.copy()
                size = len(sent)
            else:
                groups[-1].append(sent)
                centroid = (centroid + vec) / 2.0
                size += len(sent)
        return groups

    def chunk(self, docs: list[Document]) -> list[Chunk]:
        out: list[Chunk] = []
        for doc in docs:
            out.extend(_emit(doc, self._split_doc(doc), "semantic"))
        return out


@register("chunker", "agentic")
class AgenticChunker:
    """Groups consecutive sentences while they share content tokens with the
    current proposition; starts a new one when the topic shifts."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 0, min_overlap: int = 1,
                 **_: object) -> None:
        self.max_chars = chunk_size
        self.min_overlap = min_overlap

    def _toks(self, text: str) -> set[str]:
        return set(_TOKEN.findall(text.lower()))

    def chunk(self, docs: list[Document]) -> list[Chunk]:
        out: list[Chunk] = []
        for doc in docs:
            sents = _sentences(doc.text)
            groups: list[list[str]] = []
            cur: list[str] = []
            cur_tokens: set[str] = set()
            for sent in sents:
                st = self._toks(sent)
                size = sum(len(s) for s in cur)
                if cur and (len(cur_tokens & st) < self.min_overlap or size > self.max_chars):
                    groups.append(cur)
                    cur, cur_tokens = [sent], set(st)
                else:
                    cur.append(sent)
                    cur_tokens |= st
            if cur:
                groups.append(cur)
            out.extend(_emit(doc, groups, "agentic"))
        return out
