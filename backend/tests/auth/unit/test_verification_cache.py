"""The cached verification read, and what a failed lookup means (ADR-0039).

The allowance depends on this answer, so the two things worth pinning are that a
repeat read does not ask again within the TTL, and that a lookup which *fails*
answers "unverified" without turning into a fact.
"""

import logging

from ai_chat.auth.verification import VerificationStateCache


class _Clock:
    """A monotonic clock the test drives."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class _Lookup:
    """A lookup that answers from a queue and counts its calls."""

    def __init__(self, *answers: object) -> None:
        self._answers = list(answers)
        self.calls: list[str] = []

    async def __call__(self, user_id: str) -> bool:
        self.calls.append(user_id)
        answer = self._answers.pop(0) if self._answers else False
        if isinstance(answer, Exception):
            raise answer
        return bool(answer)


def _cache(lookup: _Lookup, clock: _Clock, *, ttl_seconds: float = 30.0):
    return VerificationStateCache(lookup, ttl_seconds=ttl_seconds, clock=clock)


async def test_a_repeat_read_is_answered_from_the_cache() -> None:
    clock = _Clock()
    lookup = _Lookup(True)
    cache = _cache(lookup, clock)

    assert await cache.is_verified("user-1") is True
    assert await cache.is_verified("user-1") is True

    assert lookup.calls == ["user-1"]


async def test_an_entry_expires_after_the_ttl() -> None:
    clock = _Clock()
    lookup = _Lookup(False, True)
    cache = _cache(lookup, clock, ttl_seconds=30.0)

    assert await cache.is_verified("user-1") is False

    # Inside the TTL the old answer stands; past it the state is read again —
    # which is how a just-verified account stops seeing the reduced allowance.
    clock.now = 29.0
    assert await cache.is_verified("user-1") is False

    clock.now = 31.0
    assert await cache.is_verified("user-1") is True

    assert lookup.calls == ["user-1", "user-1"]


async def test_accounts_do_not_share_an_entry() -> None:
    clock = _Clock()
    lookup = _Lookup(True, False)
    cache = _cache(lookup, clock)

    assert await cache.is_verified("user-1") is True
    assert await cache.is_verified("user-2") is False

    assert lookup.calls == ["user-1", "user-2"]


async def test_forget_drops_one_account() -> None:
    clock = _Clock()
    lookup = _Lookup(False, True)
    cache = _cache(lookup, clock)

    await cache.is_verified("user-1")
    cache.forget("user-1")

    assert await cache.is_verified("user-1") is True
    assert lookup.calls == ["user-1", "user-1"]


async def test_a_failed_lookup_is_unverified_and_not_remembered(caplog) -> None:
    clock = _Clock()
    lookup = _Lookup(RuntimeError("core is down"), True)
    cache = _cache(lookup, clock)

    with caplog.at_level(logging.WARNING):
        assert await cache.is_verified("user-1") is False

    assert "unverified" in caplog.records[0].getMessage()

    # The failure was an answer for that request, not a fact: the next one asks
    # again instead of letting an outage outlive itself.
    assert await cache.is_verified("user-1") is True
    assert lookup.calls == ["user-1", "user-1"]
