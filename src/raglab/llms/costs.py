"""Per-model price table (USD per 1K tokens) and cost computation.

Prices are approximate and easy to update in one place. Unknown models cost 0
so offline/local runs report zero cost rather than crashing.
"""

from __future__ import annotations

# (prompt_per_1k, completion_per_1k)
PRICES: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-4o": (0.0025, 0.010),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4.1": (0.002, 0.008),
    "gpt-4.1-mini": (0.0004, 0.0016),
    # OpenRouter (representative)
    "anthropic/claude-3.5-sonnet": (0.003, 0.015),
    "deepseek/deepseek-chat": (0.00014, 0.00028),
    "qwen/qwen-2.5-72b-instruct": (0.0009, 0.0009),
    "meta-llama/llama-3.1-70b-instruct": (0.0009, 0.0009),
    # Embeddings (prompt only)
    "text-embedding-3-large": (0.00013, 0.0),
    "text-embedding-3-small": (0.00002, 0.0),
}


def cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    p, c = PRICES.get(model, (0.0, 0.0))
    return (prompt_tokens / 1000.0) * p + (completion_tokens / 1000.0) * c
