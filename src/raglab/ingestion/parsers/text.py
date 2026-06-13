"""Plain-text / Markdown / HTML / CSV parsers (dependency-free)."""

from __future__ import annotations

import csv as _csv
import re
from pathlib import Path

from raglab.core.registry import register
from raglab.core.types import Document

_TAGS = re.compile(r"<[^>]+>")


@register("parser", "text")
class TextParser:
    _exts = {".txt", ".md", ".markdown", ".rst", ".log"}

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self._exts

    def parse(self, path: Path) -> list[Document]:
        text = path.read_text(encoding="utf-8", errors="replace")
        return [Document(text=text, metadata={"source": str(path), "title": path.stem})]


@register("parser", "html")
class HTMLParser:
    _exts = {".html", ".htm"}

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self._exts

    def parse(self, path: Path) -> list[Document]:
        raw = path.read_text(encoding="utf-8", errors="replace")
        text = _TAGS.sub(" ", raw)
        text = re.sub(r"\s+", " ", text).strip()
        return [Document(text=text, metadata={"source": str(path), "title": path.stem})]


@register("parser", "csv")
class CSVParser:
    _exts = {".csv", ".tsv"}

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self._exts

    def parse(self, path: Path) -> list[Document]:
        delim = "\t" if path.suffix.lower() == ".tsv" else ","
        docs: list[Document] = []
        with path.open(newline="", encoding="utf-8", errors="replace") as fh:
            for i, row in enumerate(_csv.DictReader(fh, delimiter=delim)):
                text = "\n".join(f"{k}: {v}" for k, v in row.items())
                docs.append(
                    Document(text=text, metadata={"source": str(path), "row": i})
                )
        return docs
