"""Sliding-window rate limiting on top of the ``limits`` library."""

from __future__ import annotations

import inspect
import time
from dataclasses import dataclass

from limits import parse
from limits.aio import strategies
from limits.aio.storage import RedisStorage, Storage
from limits.storage import storage_from_string

from ai_chat.shared.config import Settings

_REDIS_SCHEMES = (
    "async+redis://",
    "async+rediss://",
    "async+redis+unix://",
    "async+redis+sentinel://",
    "async+redis+cluster://",
)


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after: int


def build_storage(uri: str) -> Storage:
    """Build the async storage backend named by a ``limits``-style URI.

    ``storage_from_string`` handles ``async+memory://``; Redis needs the
    ``redispy`` implementation because this project depends on redis-py rather
    than coredis.
    """
    if uri.startswith(_REDIS_SCHEMES):
        return RedisStorage(uri, implementation="redispy", wrap_exceptions=True)
    return storage_from_string(uri)


class RateLimiter:
    """Counts requests per key with a sliding-window counter (ADR-0020).

    A sliding-window counter is used instead of a fixed window because the
    boundary burst of a fixed window would let an account spend up to twice the
    limit in a short span, and every request here can be a paid completion.
    """

    def __init__(self, storage: Storage, *, limit: str, namespace: str = "rate-limit") -> None:
        self._storage = storage
        self._strategy = strategies.SlidingWindowCounterRateLimiter(storage)
        self._limit = parse(limit)
        self._namespace = namespace

    async def check(self, key: str) -> RateLimitDecision:
        allowed = await self._strategy.hit(self._limit, self._namespace, key)
        stats = await self._strategy.get_window_stats(self._limit, self._namespace, key)
        return RateLimitDecision(
            allowed=allowed,
            remaining=stats.remaining,
            retry_after=max(0, int(stats.reset_time - time.time())),
        )

    async def aclose(self) -> None:
        """Release the storage connection, if the backend has one."""
        close = getattr(self._storage, "close", None)
        if close is None:
            return
        result = close()
        if inspect.isawaitable(result):
            await result


def build_rate_limiter(settings: Settings) -> RateLimiter:
    return RateLimiter(
        build_storage(settings.rate_limit_storage_uri),
        limit=settings.rate_limit_chat,
    )
