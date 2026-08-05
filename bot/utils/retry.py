"""Resilience helpers: async retry with exponential back-off + jitter."""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable, Sequence
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def retry_async(
    func: Callable[[], Awaitable[T]],
    *,
    attempts: int,
    base_delay: float,
    exceptions: Sequence[type[BaseException]] = (Exception,),
    is_retryable: Callable[[BaseException], bool] | None = None,
    on_retry: Callable[[int, int, BaseException], Awaitable[None]] | None = None,
) -> T:
    """Call ``func`` up to ``attempts`` times, backing off exponentially.

    ``is_retryable`` — when provided — can veto a retry (e.g. for fatal
    errors that will never succeed). ``on_retry(attempt, total, exc)`` is
    awaited between attempts so callers can surface progress to the user.
    """
    last_exc: BaseException | None = None

    for attempt in range(1, attempts + 1):
        try:
            return await func()
        except exceptions as exc:  # noqa: PERF203
            last_exc = exc
            if is_retryable is not None and not is_retryable(exc):
                raise
            if attempt < attempts:
                if on_retry is not None:
                    await on_retry(attempt, attempts, exc)
                delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                logger.warning(
                    "Retry %d/%d after error (%s); sleeping %.1fs",
                    attempt,
                    attempts,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)

    assert last_exc is not None
    raise last_exc
