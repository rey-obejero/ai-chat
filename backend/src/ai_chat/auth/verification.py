"""The email-verification state, read through a short-lived in-process cache.

The state lives in the auth service, and the app reads it on a hot path: every
quota check and every `/me` needs to know whether the account is verified
(ADR-0039). The cache keeps that read off the network per request, while staying
short enough that clicking the link is visible almost immediately; `forget`
makes it exact when the app itself completes the verification.

A failed lookup is answered **unverified**, and is not cached. That is the
conservative direction: an outage must not grant the full allowance to an
account nobody has proved anything about. It is not treated as a fact either —
the next request asks again rather than letting a blip outlive itself.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)

# Short on purpose: the cost of a stale entry is a verified account still seeing
# the reduced allowance, and the app cannot see the verify call coming (the
# SuperTokens middleware answers it), so only the TTL bounds that staleness.
TTL_SECONDS = 30.0

Lookup = Callable[[str], Awaitable[bool]]


class VerificationStateCache:
    """``is this account's email verified``, remembered for a short TTL."""

    def __init__(
        self,
        lookup: Lookup,
        *,
        ttl_seconds: float = TTL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._lookup = lookup
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._entries: dict[str, tuple[float, bool]] = {}

    def cached(self, user_id: str) -> bool | None:
        """The remembered answer, or ``None`` when there is none to trust."""
        entry = self._entries.get(user_id)
        if entry is None:
            return None
        expires_at, verified = entry
        if expires_at <= self._clock():
            del self._entries[user_id]
            return None
        return verified

    async def is_verified(self, user_id: str) -> bool:
        remembered = self.cached(user_id)
        if remembered is not None:
            return remembered

        try:
            verified = await self._lookup(user_id)
        except Exception:
            logger.warning(
                "Email verification lookup failed; treating the account as unverified",
                extra={"user_id": user_id},
                exc_info=True,
            )
            return False

        self._entries[user_id] = (self._clock() + self._ttl_seconds, verified)
        return verified

    def forget(self, user_id: str) -> None:
        """Drop one account's entry, so the next read asks the auth service."""
        self._entries.pop(user_id, None)

    def clear(self) -> None:
        self._entries.clear()
