"""Evaluation: built-in proxy metrics, RAGAS, LLM judges, and reports.

Importing this package registers every evaluator with the registry
(``builtin``, ``ragas``, ``llm_judge``) so ``registry.available("evaluator")``
is complete after :func:`raglab.core.registry.bootstrap`.
"""

from raglab.evaluation import (  # noqa: F401
    builtin,
    llm_judges,
    ragas_eval,
    reports,
)
