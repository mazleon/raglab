"""OpenAI chat adapter (Chat Completions API).

Behaviour lives on the shared :class:`~raglab.llms._openai_compat.OpenAICompatLLM`
base; this module only pins the OpenAI defaults and registers the ``openai`` LLM.
"""

from __future__ import annotations

from raglab.core.registry import register
from raglab.llms._openai_compat import OpenAICompatLLM


@register("llm", "openai")
class OpenAILLM(OpenAICompatLLM):
    _default_model = "gpt-4o-mini"
    _api_key_env = "OPENAI_API_KEY"
    _provider = "openai"