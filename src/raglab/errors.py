"""RAGLab exception hierarchy + a provider-agnostic retry helper.

Every failure RAGLab can surface inherits from :class:`RaglabError`, so callers
(CLI, API, benchmark runner) can catch one base type and present a clean message
instead of a raw stack trace from a third-party SDK.

Failures are split into two intents:
  * **fatal**     — config/auth/model mistakes; retrying cannot help. Fail fast.
  * **transient** — rate limits, timeouts, 5xx; worth retrying with backoff.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger("raglab")

T = TypeVar("T")


class RaglabError(Exception):
    """Base class for every error RAGLab raises deliberately."""


class ConfigError(RaglabError):
    """Invalid or inconsistent configuration."""


class AuthError(RaglabError):
    """Authentication or authorization failure (HTTP 401)."""


class MissingDependencyError(RaglabError):
    """A required optional dependency (extra) is not installed."""


class ProviderError(RaglabError):
    """A call to an external provider (LLM / embeddings / rerank) failed."""


class ProviderAuthError(ProviderError):
    """Missing or invalid API key (HTTP 401/403)."""


class ModelNotFoundError(ProviderError):
    """The requested model id does not exist or is not available (HTTP 404)."""


class ProviderRateLimitError(ProviderError):
    """Rate limit not cleared after exhausting retries (HTTP 429)."""


class ProviderResponseError(ProviderError):
    """The provider returned an empty or malformed response."""


def call_with_retries(
    fn: Callable[[], T],
    *,
    is_fatal: Callable[[Exception], RaglabError | None],
    is_transient: Callable[[Exception], bool],
    max_retries: int = 4,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retry_after: Callable[[Exception], float | None] | None = None,
    label: str = "provider call",
) -> T:
    """Run ``fn`` with exponential backoff on transient errors.

    ``is_fatal`` maps an exception to a :class:`RaglabError` to raise immediately
    (e.g. a bad model -> ModelNotFoundError); return ``None`` to let other
    classifiers run. ``is_transient`` decides whether to retry. ``retry_after``
    may extract a server-advised delay (seconds) from the exception.
    """

    last: Exception | None = None
    for attempt in range(max_retries):
        try:
            return fn()
        except RaglabError:
            raise
        except Exception as exc:  # noqa: BLE001 - we re-classify below
            fatal = is_fatal(exc)
            if fatal is not None:
                raise fatal from exc
            if not is_transient(exc):
                raise ProviderError(f"{label} failed: {exc}") from exc
            last = exc
            delay = min(base_delay * (2**attempt), max_delay)
            if retry_after is not None:
                advised = retry_after(exc)
                if advised is not None:
                    delay = min(max(delay, advised), 60.0)
            logger.warning(
                "%s transient error (attempt %d/%d): %s — retrying in %.1fs",
                label, attempt + 1, max_retries, exc, delay,
            )
            time.sleep(delay)
    raise ProviderRateLimitError(
        f"{label} failed after {max_retries} attempts: {last}"
    ) from last
