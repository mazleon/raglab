"""Local sentence-transformers embedders (BGE / E5). Requires the ``local`` extra."""

from __future__ import annotations

from raglab.core.registry import register
from raglab.core.types import Vector

_DEFAULTS = {"bge_local": "BAAI/bge-small-en-v1.5", "e5_local": "intfloat/e5-small-v2"}


class _SentenceTransformerEmbedder:
    _default_model = ""
    # E5/BGE expect instruction prefixes for best retrieval quality.
    _query_prefix = ""
    _doc_prefix = ""

    def __init__(self, model: str | None = None, dim: int | None = None, **_: object) -> None:
        self._model_name = model or self._default_model
        self._model = None
        self._dim = dim  # filled lazily from the model if not provided

    def _ensure(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:  # pragma: no cover
                raise ImportError(
                    "Local embeddings need the 'local' extra: pip install 'raglab[local]'"
                ) from e
            model = SentenceTransformer(self._model_name)
            self._model = model
            if self._dim is None:
                self._dim = int(model.get_sentence_embedding_dimension())
        return self._model

    @property
    def dim(self) -> int:
        if self._dim is None:
            self._ensure()
        return int(self._dim or 0)

    def embed_documents(self, texts: list[str]) -> list[Vector]:
        model = self._ensure()
        prefixed = [self._doc_prefix + t for t in texts]
        vecs = model.encode(prefixed, normalize_embeddings=True)
        return [v.tolist() for v in vecs]

    def embed_query(self, text: str) -> Vector:
        model = self._ensure()
        vec = model.encode([self._query_prefix + text], normalize_embeddings=True)[0]
        return vec.tolist()


@register("embedder", "bge_local")
class BGEEmbedder(_SentenceTransformerEmbedder):
    _default_model = _DEFAULTS["bge_local"]
    _query_prefix = "Represent this sentence for searching relevant passages: "


@register("embedder", "e5_local")
class E5Embedder(_SentenceTransformerEmbedder):
    _default_model = _DEFAULTS["e5_local"]
    _query_prefix = "query: "
    _doc_prefix = "passage: "
