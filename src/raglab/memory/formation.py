"""Memory Formation Engine — decides what is worth remembering.

A gate on writes: trivial or low-importance content is dropped, salient content
is kept, and over-long content is flagged for summarization. This is what keeps
the memory store signal-rich rather than a dumping ground.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FormationDecision:
    action: str  # "remember" | "summarize" | "forget"
    reason: str


class MemoryFormationEngine:
    def __init__(
        self, importance_threshold: float = 0.3, summarize_chars: int = 4000
    ) -> None:
        self.importance_threshold = importance_threshold
        self.summarize_chars = summarize_chars

    def decide(self, content: str, importance: float) -> FormationDecision:
        if not content.strip():
            return FormationDecision("forget", "empty content")
        if importance < self.importance_threshold:
            return FormationDecision("forget", f"importance {importance:.2f} below threshold")
        if len(content) > self.summarize_chars:
            return FormationDecision("summarize", "content too long; summarize before storing")
        return FormationDecision("remember", "salient")

    def should_remember(self, content: str, importance: float) -> bool:
        return self.decide(content, importance).action != "forget"
