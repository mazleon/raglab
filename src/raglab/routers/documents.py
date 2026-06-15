"""Document upload, listing, and deletion — real ingestion, per tenant.

Upload saves the file, registers it (status ``indexing``), parses → chunks →
embeds → upserts into the tenant's Qdrant collection, then flips the record to
``indexed`` (or ``failed`` with the error). The endpoint is a sync ``def`` so
FastAPI runs the blocking ingest in its threadpool.
"""

from __future__ import annotations

import contextlib
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from raglab.accounts.auth import User
from raglab.errors import RaglabError
from raglab.ingestion import store as docstore
from raglab.ingestion.store import DocumentRecord
from raglab.server.deps import current_user
from raglab.server.sessions import build_session_config, ingest_file, tenant_collection

logger = logging.getLogger("raglab.documents")

router = APIRouter(prefix="/documents", tags=["documents"])

_SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown", ".rst", ".log", ".html", ".htm",
                       ".csv", ".tsv", ".pdf", ".docx"}


def _upload_dir(tenant_id: str) -> Path:
    base = Path(os.environ.get("RAGLAB_UPLOAD_DIR", "uploads")) / tenant_id
    base.mkdir(parents=True, exist_ok=True)
    return base


@router.get("")
def list_docs(user: User = Depends(current_user)) -> dict[str, Any]:
    rows = docstore.list_documents(user.tenant_id)
    return {"documents": [d.to_dict() for d in rows], "count": len(rows)}


@router.post("")
def upload(
    file: UploadFile = File(...),
    embedding: str = Form("hashing"),
    user: User = Depends(current_user),
) -> dict[str, Any]:
    filename = file.filename or "upload.txt"
    suffix = Path(filename).suffix.lower()
    if suffix not in _SUPPORTED_SUFFIXES:
        raise HTTPException(400, f"unsupported file type: {suffix or 'unknown'}")

    import uuid

    data = file.file.read()
    doc_id = uuid.uuid4().hex
    dest = _upload_dir(user.tenant_id) / f"{doc_id}_{filename}"
    dest.write_bytes(data)

    record = DocumentRecord(
        id=doc_id, tenant_id=user.tenant_id, name=filename,
        type=file.content_type or suffix, size=len(data), status="indexing",
        embedding=embedding, collection=tenant_collection(user.tenant_id, embedding),
        path=str(dest),
    )
    record = docstore.create(record)

    try:
        cfg = build_session_config(
            tenant_id=user.tenant_id, overrides={"embedding": {"name": embedding}}
        )
        chunks = ingest_file(cfg, dest)
        docstore.update_status(record.id, "indexed", chunks=chunks)
    except RaglabError as exc:
        docstore.update_status(record.id, "failed", error=str(exc))
        raise HTTPException(400, f"ingestion failed: {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("upload failed")
        docstore.update_status(record.id, "failed", error=str(exc))
        raise HTTPException(500, "ingestion failed") from exc

    fresh = docstore.get(user.tenant_id, record.id)
    return {"document": fresh.to_dict() if fresh else record.to_dict()}


@router.delete("/{doc_id}")
def delete(doc_id: str, user: User = Depends(current_user)) -> dict[str, bool]:
    record = docstore.get(user.tenant_id, doc_id)
    if record and record.path:
        with contextlib.suppress(OSError):
            Path(record.path).unlink(missing_ok=True)
    return {"deleted": docstore.delete(user.tenant_id, doc_id)}
