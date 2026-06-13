"""Document parsers + an extension-based dispatcher."""

from __future__ import annotations

from pathlib import Path

from raglab.core import registry
from raglab.core.interfaces import Parser
from raglab.core.types import Document
from raglab.ingestion.parsers import pdf, text  # noqa: F401


def parser_for(path: Path) -> Parser | None:
    """Return the first registered parser that supports ``path``."""

    for name in registry.available("parser"):
        parser: Parser = registry.create("parser", name)
        if parser.supports(path):
            return parser
    return None


def parse_path(path: Path) -> list[Document]:
    parser = parser_for(path)
    if parser is None:
        # Best-effort fallback: treat as UTF-8 text.
        return registry.create("parser", "text").parse(path)
    return parser.parse(path)
