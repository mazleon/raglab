"""Adaptive RAG: a router classifies query complexity and delegates to the most
appropriate strategy — Naive for simple, Hybrid for moderate, Agentic for
complex — so cost/latency scale with difficulty."""

from __future__ import annotations

from raglab.agents.reasoning import classify_complexity
from raglab.core.registry import create, register
from raglab.core.types import RAGResult, TrajectoryStep
from raglab.pipelines.base import BasePipeline

_ROUTE = {"simple": "naive_rag", "moderate": "hybrid_rag", "complex": "agentic_rag"}


@register("architecture", "adaptive_rag")
class AdaptiveRAG(BasePipeline):
    name = "adaptive_rag"

    def run(self, query: str) -> RAGResult:
        complexity = classify_complexity(query, self.c.llm)
        target = _ROUTE[complexity]
        delegate = create("architecture", target, components=self.c)
        result = delegate.run(query)
        result.architecture = self.name
        result.trajectory.insert(
            0, TrajectoryStep("route", f"{complexity} -> {target}")
        )
        return result
