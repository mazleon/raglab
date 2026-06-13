"""Metadata enrichment for chunks (timestamp, ordering, section hints)."""

from __future__ import annotations

from datetime import datetime, timezone

from raglab.core.types import Chunk


def enrich(chunks: list[Chunk]) -> list[Chunk]:
    ts = datetime.now(timezone.utc).isoformat()
    for i, chunk in enumerate(chunks):
        chunk.metadata.setdefault("timestamp", ts)
        chunk.metadata.setdefault("chunk_id", chunk.chunk_id)
        chunk.metadata.setdefault("document_id", chunk.document_id)
        chunk.metadata.setdefault("global_index", i)
        # Cheap section hint: first markdown heading in the chunk, if any.
        for line in chunk.text.splitlines():
            if line.startswith("#"):
                chunk.metadata.setdefault("section", line.lstrip("# ").strip())
                break
    return chunks
