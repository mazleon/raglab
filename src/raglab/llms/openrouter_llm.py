"""OpenRouter chat adapter.

OpenRouter speaks the OpenAI Chat Completions API, so it subclasses the shared
:class:`~raglab.llms._openai_compat.OpenAICompatLLM` base and only pins the
OpenRouter base URL, key env, and a sensible default model.
"""

from __future__ import annotations

from raglab.core.registry import register
from raglab.llms._openai_compat import OpenAICompatLLM


@register("llm", "openrouter")
class OpenRouterLLM(OpenAICompatLLM):
    # A reliable, low-cost default. Free ``:free`` slugs are rate-limited and
    # frequently require the paid slug, so they are a poor default.
    _default_model = "deepseek/deepseek-chat"
    _base_url = "https://openrouter.ai/api/v1"
    _api_key_env = "OPENROUTER_API_KEY"
    _provider = "openrouter"