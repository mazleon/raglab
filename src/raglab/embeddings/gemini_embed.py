"""Google Gemini embeddings adapter (requires ``providers`` extra + GOOGLE_API_KEY).

Uses the current ``google-genai`` SDK. ``gemini-embedding-001`` supports a
configurable output dimensionality; we default to 768 to keep vector stores
compact.
"""

from __future__ import annotations

import os
from typing import Any

from raglab.core.registry import register
from raglab.core.types import Vector


@register("embedder", "gemini")
class GeminiEmbedder:
    def __init__(self, model: str | None = None, dim: int | None = None, **_: object) -> None:
        self._model = model or "gemini-embedding-001"
        self._dim = int(dim or 768)
        self._client: Any = None

    def _ensure(self):
        if self._client is None:
            try:
                from google import genai
            except ImportError as e:  # pragma: no cover
                raise ImportError(
                    "Gemini embeddings need the 'providers' extra: pip install 'raglab[providers]'"
                ) from e
            self._client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        return self._client

    @property
    def dim(self) -> int:
        return self._dim

    def _embed(self, texts: list[str], task_type: str) -> list[Vector]:
        client = self._ensure()
        from google.genai import types

        resp = client.models.embed_content(
            model=self._model,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type=task_type, output_dimensionality=self._dim
            ),
        )
        return [list(e.values) for e in resp.embeddings]

    def embed_documents(self, texts: list[str]) -> list[Vector]:
        return self._embed(texts, "RETRIEVAL_DOCUMENT")

    def embed_query(self, text: str) -> Vector:
        return self._embed([text], "RETRIEVAL_QUERY")[0]
