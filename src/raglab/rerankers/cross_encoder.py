"""Local cross-encoder reranker (requires the ``local`` extra)."""

from __future__ import annotations

from raglab.core.registry import register
from raglab.core.types import ScoredChunk


@register("reranker", "cross_encoder")
class CrossEncoderReranker:
    def __init__(self, model: str | None = None, **_: object) -> None:
        self._model_name = model or "cross-encoder/ms-marco-MiniLM-L-6-v2"
        self._model = None

    def _ensure(self):
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
            except ImportError as e:  # pragma: no cover
                raise ImportError(
                    "Cross-encoder reranking needs the 'local' extra: "
                    "pip install 'raglab[local]'"
                ) from e
            self._model = CrossEncoder(self._model_name)
        return self._model

    def rerank(
        self, query: str, chunks: list[ScoredChunk], top_n: int
    ) -> list[ScoredChunk]:
        if not chunks:
            return []
        model = self._ensure()
        scores = model.predict([(query, c.text) for c in chunks])
        ranked = sorted(
            (ScoredChunk(c.chunk, float(s)) for c, s in zip(chunks, scores, strict=True)),
            key=lambda s: s.score,
            reverse=True,
        )
        return ranked[:top_n]
