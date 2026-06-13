"""High-level orchestration shared by the CLI, API, and benchmark runner.

Keeps the composition logic (build components -> optionally ingest -> build
pipeline -> run with tracing) in one place so every entrypoint behaves
identically.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from raglab.core.config import (
    Components,
    ExperimentConfig,
    build_chunker,
    build_components,
    build_pipeline_from_components,
)
from raglab.core.interfaces import Pipeline
from raglab.core.types import RAGResult
from raglab.ingestion.pipeline import IngestionPipeline
from raglab.observability.tracer import Tracer, build_tracer


@dataclass
class Engine:
    config: ExperimentConfig
    components: Components
    pipeline: Pipeline
    tracer: Tracer

    def ingest(self, path: str | Path) -> int:
        ing = IngestionPipeline(
            build_chunker(self.config.chunker),
            self.components.embedder,
            self.components.store,
        )
        return ing.ingest(path).chunks

    def answer(self, query: str) -> RAGResult:
        with self.tracer.span(
            f"query:{self.config.architecture}", query=query
        ):
            result = self.pipeline.run(query)
        self.tracer.flush()
        return result


def build_engine(config: ExperimentConfig, ingest_path: str | Path | None = None) -> Engine:
    from raglab.env import ensure_loaded

    ensure_loaded()
    components = build_components(config)
    pipeline = build_pipeline_from_components(config, components)
    tracer = build_tracer(config.observability)
    engine = Engine(config, components, pipeline, tracer)
    if ingest_path is not None:
        engine.ingest(ingest_path)
    return engine
