"""Compressed retrieval experiment (Phase 6, TurboVec/TurboQuant-inspired).

Quantizes chunk embeddings to a fraction of their memory and searches in the
compressed space:

  * ``binary`` — 1 bit/dim (sign). Similarity = agreement count over {-1,+1}.
    ~32x smaller than float32; the classic binary-quantization trick.
  * ``int8``   — 8 bits/dim (per-vector scalar quantization). ~4x smaller.

Exposes ``compression_ratio`` so benchmarks can trade recall against memory.
The index is built in-memory from the vector store's chunks via the embedder.
"""

from __future__ import annotations

import numpy as np

from raglab.core.interfaces import Embedder, VectorStore
from raglab.core.registry import register
from raglab.core.types import Chunk, ScoredChunk


@register("retriever", "compressed")
class CompressedRetriever:
    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        mode: str = "binary",
        **_: object,
    ) -> None:
        self.embedder = embedder
        self.store = store
        self.mode = mode
        self._chunks: list[Chunk] = []
        self._codes: np.ndarray | None = None
        self._scales: np.ndarray | None = None

    # ---- quantization ----
    def _quantize(self, vecs: np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
        if self.mode == "binary":
            return np.where(vecs >= 0, 1, -1).astype(np.int8), None
        # int8 per-vector scalar quantization
        scales = np.abs(vecs).max(axis=1, keepdims=True)
        scales[scales == 0] = 1.0
        codes = np.clip(np.round(vecs / scales * 127), -127, 127).astype(np.int8)
        return codes, scales

    def _ensure_index(self) -> None:
        if self._codes is not None:
            return
        self._chunks = self.store.all_chunks()
        if not self._chunks:
            self._codes = np.zeros((0, 1), dtype=np.int8)
            return
        vecs = np.asarray(
            self.embedder.embed_documents([c.text for c in self._chunks]),
            dtype=np.float32,
        )
        self._codes, self._scales = self._quantize(vecs)

    @property
    def compression_ratio(self) -> float:
        """Approximate memory saving vs float32 (32 bits/dim)."""

        return 32.0 if self.mode == "binary" else 4.0

    def retrieve(self, query: str, k: int) -> list[ScoredChunk]:
        self._ensure_index()
        if self._codes is None or len(self._chunks) == 0:
            return []
        q = np.asarray(self.embedder.embed_query(query), dtype=np.float32)
        if self.mode == "binary":
            qc = np.where(q >= 0, 1, -1).astype(np.int8)
            scores = self._codes @ qc  # agreement count
        else:
            qscale = np.abs(q).max() or 1.0
            qc = np.clip(np.round(q / qscale * 127), -127, 127).astype(np.int16)
            scores = (self._codes.astype(np.int16) @ qc).astype(np.float32)
        top = np.argsort(-scores)[:k]
        return [ScoredChunk(self._chunks[i], float(scores[i])) for i in top]
