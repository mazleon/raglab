"""Deterministic, dependency-free embedder.

Hashes tokens into a fixed-dimensional bag-of-words vector with signed buckets,
then L2-normalises. It carries no semantics beyond lexical overlap, but it lets
the entire platform run and be tested offline with zero API keys or model
downloads. Swap to ``openai``/``cohere``/``bge_local`` for real semantics.
"""

from __future__ import annotations

import hashlib
import re

import numpy as np

from raglab.core.registry import register
from raglab.core.types import Vector

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


@register("embedder", "hashing")
class HashingEmbedder:
    def __init__(self, model: str | None = None, dim: int | None = None, **_: object) -> None:
        self._dim = int(dim or 384)

    @property
    def dim(self) -> int:
        return self._dim

    def _embed_one(self, text: str) -> Vector:
        vec = np.zeros(self._dim, dtype=np.float32)
        for tok in _tokenize(text):
            digest = hashlib.md5(tok.encode()).digest()
            idx = int.from_bytes(digest[:4], "little") % self._dim
            sign = 1.0 if digest[4] & 1 else -1.0
            vec[idx] += sign
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm
        return vec.tolist()

    def embed_documents(self, texts: list[str]) -> list[Vector]:
        return [self._embed_one(t) for t in texts]

    def embed_query(self, text: str) -> Vector:
        return self._embed_one(text)
