"""Backward-compat re-export.

The error hierarchy now lives in :mod:`raglab.core.errors` (it is a core
concern and ``core`` should not reach up to a sibling module). This module
re-exports the public names so existing ``from raglab.errors import ...`` calls
keep working; new code should import from ``raglab.core.errors``.
"""

from raglab.core.errors import (  # noqa: F401
    AuthError,
    ConfigError,
    MissingDependencyError,
    ModelNotFoundError,
    ProviderAuthError,
    ProviderError,
    ProviderRateLimitError,
    ProviderResponseError,
    RaglabError,
    call_with_retries,
)