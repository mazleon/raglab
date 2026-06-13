"""Embedding adapters. Importing the package registers every embedder."""

from raglab.embeddings import (  # noqa: F401
    cohere_embed,
    gemini_embed,
    hashing,
    local_embed,
    openai_embed,
)
