"""RAGAS evaluation (requires the ``eval`` extra + a judge LLM).

Wraps RAGAS so the rest of RAGLab depends only on the ``Evaluator`` protocol.
Imports are lazy so the package loads without ragas installed.
"""

from __future__ import annotations

from typing import Any

_DEFAULT_METRICS = [
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
]


class RagasEvaluator:
    def __init__(self, metrics: list[str] | None = None, llm: Any = None) -> None:
        self.metric_names = metrics or _DEFAULT_METRICS
        self.llm = llm

    def evaluate(self, records: list[dict[str, Any]]) -> dict[str, float]:
        try:
            import ragas
            from datasets import Dataset
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "RAGAS evaluation needs the 'eval' extra: pip install 'raglab[eval]'"
            ) from e

        ds = Dataset.from_list(
            [
                {
                    "question": r.get("question", ""),
                    "answer": r.get("answer", ""),
                    "contexts": r.get("contexts", []),
                    "ground_truth": r.get("ground_truth", ""),
                }
                for r in records
            ]
        )
        result = ragas.evaluate(ds)  # uses env-configured judge by default
        # Normalise to a plain dict of floats.
        scores: dict[str, float] = {}
        for k, v in dict(result).items():
            try:
                scores[k] = float(v)
            except (TypeError, ValueError):
                continue
        return scores
