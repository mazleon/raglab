"""OpenAI embeddings adapter (requires the ``providers`` extra + OPENAI_API_KEY)."""

from __future__ import annotations

from raglab.core.registry import register
from raglab.core.types import Vector

_DIMS = {
    "text-embedding-3-large": 3072,
    "text-embedding-3-small": 1536,
    "text-embedding-ada-002": 1536,
}


@register("embedder", "openai")
class OpenAIEmbedder:
    def __init__(self, model: str | None = None, dim: int | None = None, **_: object) -> None:
        self._model = model or "text-embedding-3-large"
        self._dim = int(dim or _DIMS.get(self._model, 3072))
        self._client = None

    def _ensure(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as e:  # pragma: no cover
                raise ImportError(
                    "OpenAI embeddings need the 'providers' extra: pip install 'raglab[providers]'"
                ) from e
            self._client = OpenAI()
        return self._client

    @property
    def dim(self) -> int:
        return self._dim

    def embed_documents(self, texts: list[str]) -> list[Vector]:
        client = self._ensure()
        resp = client.embeddings.create(model=self._model, input=texts)
        return [d.embedding for d in resp.data]

    def embed_query(self, text: str) -> Vector:
        return self.embed_documents([text])[0]
