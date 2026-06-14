"""Cohere embeddings adapter (requires the ``providers`` extra + COHERE_API_KEY)."""

from __future__ import annotations

import os
from typing import Any

from raglab.core.registry import register
from raglab.core.types import Vector
from raglab.errors import MissingDependencyError, ProviderAuthError

_DIMS = {"embed-english-v3.0": 1024, "embed-multilingual-v3.0": 1024}


@register("embedder", "cohere")
class CohereEmbedder:
    def __init__(self, model: str | None = None, dim: int | None = None, **_: object) -> None:
        self._model = model or "embed-english-v3.0"
        self._dim = int(dim or _DIMS.get(self._model, 1024))
        self._client: Any = None

    def _ensure(self):
        if self._client is None:
            try:
                import cohere
            except ImportError as e:
                raise MissingDependencyError(
                    "Cohere embeddings need the 'providers' extra: pip install 'raglab[providers]'"
                ) from e
            api_key = os.environ.get("COHERE_API_KEY")
            if not api_key:
                raise ProviderAuthError(
                    "cohere: environment variable COHERE_API_KEY is not set."
                )
            self._client = cohere.Client(api_key)
        return self._client

    @property
    def dim(self) -> int:
        return self._dim

    def _embed(self, texts: list[str], input_type: str) -> list[Vector]:
        client = self._ensure()
        resp = client.embed(texts=texts, model=self._model, input_type=input_type)
        return [list(v) for v in resp.embeddings]

    def embed_documents(self, texts: list[str]) -> list[Vector]:
        return self._embed(texts, "search_document")

    def embed_query(self, text: str) -> Vector:
        return self._embed([text], "search_query")[0]
