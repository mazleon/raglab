"""LLM-as-judge evaluators.

Each judge prompts a (configurable, swappable) LLM to score one quality
dimension on a 0..1 scale. The judge model is itself any registered ``LLM``, so
you can compare judges by swapping the model in config.
"""

from __future__ import annotations

import re
from typing import Any

from raglab.core.interfaces import LLM

_FLOAT = re.compile(r"[01](?:\.\d+)?")

_RUBRICS: dict[str, str] = {
    "faithfulness": (
        "Score how fully the ANSWER is supported by the CONTEXT (no unsupported "
        "claims). 1.0 = every claim is grounded, 0.0 = fabricated."
    ),
    "grounding": (
        "Score whether the ANSWER stays within the CONTEXT and avoids outside "
        "knowledge. 1.0 = entirely grounded."
    ),
    "citation": (
        "Score whether the ANSWER cites the correct supporting sources. "
        "1.0 = well cited, 0.0 = no/incorrect citations."
    ),
    "answer_quality": (
        "Score the ANSWER's correctness and relevance to the QUESTION given the "
        "GROUND_TRUTH. 1.0 = excellent."
    ),
    "reasoning": (
        "Score the logical soundness of the ANSWER's reasoning. 1.0 = sound."
    ),
}


class LLMJudge:
    def __init__(self, dimension: str, llm: LLM) -> None:
        if dimension not in _RUBRICS:
            raise ValueError(f"Unknown judge dimension {dimension!r}")
        self.dimension = dimension
        self.llm = llm

    def _score_one(self, record: dict[str, Any]) -> float:
        prompt = (
            f"{_RUBRICS[self.dimension]}\n\n"
            f"QUESTION: {record.get('question', '')}\n"
            f"GROUND_TRUTH: {record.get('ground_truth', '')}\n"
            f"CONTEXT:\n{chr(10).join(record.get('contexts', []))}\n"
            f"ANSWER: {record.get('answer', '')}\n\n"
            "Respond with ONLY a number between 0 and 1."
        )
        resp = self.llm.generate(
            [
                {"role": "system", "content": "You are a strict evaluation judge."},
                {"role": "user", "content": prompt},
            ]
        )
        match = _FLOAT.search(resp.text)
        return float(match.group()) if match else 0.0

    def evaluate(self, records: list[dict[str, Any]]) -> dict[str, float]:
        if not records:
            return {f"judge_{self.dimension}": 0.0}
        mean = sum(self._score_one(r) for r in records) / len(records)
        return {f"judge_{self.dimension}": round(mean, 4)}
