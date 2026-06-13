"""Text cleaning applied to parsed documents before chunking."""

from __future__ import annotations

import re

from raglab.core.types import Document

_WS = re.compile(r"[ \t]+")
_NL = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\x00", "")
    text = _WS.sub(" ", text)
    text = _NL.sub("\n\n", text)
    return text.strip()


def clean_documents(docs: list[Document]) -> list[Document]:
    for doc in docs:
        doc.text = clean_text(doc.text)
    return [d for d in docs if d.text]
