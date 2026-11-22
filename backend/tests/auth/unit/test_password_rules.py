"""Password screening: length, entropy, and breach data (FR-2, ADR-0038).

The breach check is the only part that leaves the process, so it sits behind a
port here: every test injects a fake, and the one test about the service being
unreachable asserts the fail-open behaviour rather than a refusal.
"""

import logging

import pytest

from ai_chat.auth.exceptions import WeakPasswordError
from ai_chat.auth.passwords import split_sha1, validate_password
from ai_chat.shared.config import Settings

# Long, unguessable, and scores 4 with zxcvbn — the case that must be accepted.
STRONG = "correcthorsebatterystaple"

# Longer than the 72 characters `zxcvbn` will score, so it pins the cap: the
# phrase is judged on its prefix rather than refused outright.
LONG_PASSPHRASE = "Masquerade-Lantern-Obsidian-Quilt-Riptide-Saffron-Tundra-Vertex-Kx7#Qm2!Vt9"


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)


class _FakeBreachClient:
    """Stands in for the HIBP lookup: no network, and it records the prefixes."""

    def __init__(self, *, breached: set[str] | None = None, error: Exception | None = None):
        self._breached = breached or set()
        self._error = error
        self.prefixes: list[str] = []

    async def known_suffixes(self, sha1_prefix: str) -> set[str]:
        self.prefixes.append(sha1_prefix)
        if self._error is not None:
            raise self._error
        return self._breached


async def test_a_password_under_eight_characters_is_refused() -> None:
    with pytest.raises(WeakPasswordError) as refused:
        await validate_password("Aa1!xy", settings=_settings(password_breach_check_enabled=False))

    assert "8 characters" in refused.value.detail


async def test_a_weak_password_is_refused() -> None:
    with pytest.raises(WeakPasswordError) as refused:
        await validate_password(
            "password123", settings=_settings(password_breach_check_enabled=False)
        )

    assert "too easy to guess" in refused.value.detail


async def test_the_minimum_score_is_a_setting() -> None:
    # `hunter2hunter2` scores 1: under the default floor of 2, at or above 1.
    with pytest.raises(WeakPasswordError):
        await validate_password(
            "hunter2hunter2", settings=_settings(password_breach_check_enabled=False)
        )

    await validate_password(
        "hunter2hunter2",
        settings=_settings(password_breach_check_enabled=False, password_min_score=1),
    )


async def test_a_breached_password_is_refused() -> None:
    _, suffix = split_sha1(STRONG)
    client = _FakeBreachClient(breached={suffix})

    with pytest.raises(WeakPasswordError) as refused:
        await validate_password(STRONG, settings=_settings(), breach_client=client)

    assert "data breach" in refused.value.detail


async def test_a_strong_unbreached_password_is_accepted() -> None:
    client = _FakeBreachClient(breached={"0000000000000000000000000000000000000"})

    await validate_password(STRONG, settings=_settings(), breach_client=client)

    assert client.prefixes == [split_sha1(STRONG)[0]]


async def test_only_the_hash_prefix_leaves_the_server() -> None:
    client = _FakeBreachClient()

    await validate_password(STRONG, settings=_settings(), breach_client=client)

    prefix, suffix = split_sha1(STRONG)
    assert client.prefixes == [prefix]
    # Five characters is all the lookup needs, and all it may have.
    assert len(prefix) == 5
    assert suffix not in client.prefixes


async def test_an_unreachable_breach_service_does_not_block_sign_up(caplog) -> None:
    client = _FakeBreachClient(error=RuntimeError("connection refused"))

    with caplog.at_level(logging.WARNING):
        await validate_password(STRONG, settings=_settings(), breach_client=client)

    assert client.prefixes  # it was tried
    assert [record.levelname for record in caplog.records] == ["WARNING"]
    assert "breach check unavailable" in caplog.records[0].getMessage()


async def test_the_breach_check_can_be_switched_off() -> None:
    client = _FakeBreachClient(error=AssertionError("the lookup must not be reached"))

    await validate_password(
        STRONG,
        settings=_settings(password_breach_check_enabled=False),
        breach_client=client,
    )

    assert client.prefixes == []


async def test_a_passphrase_longer_than_the_scorer_reads_is_accepted() -> None:
    """`zxcvbn` raises above 72 characters; a long passphrase is judged, not refused."""
    assert len(LONG_PASSPHRASE) > 72

    await validate_password(
        LONG_PASSPHRASE, settings=_settings(password_breach_check_enabled=False)
    )


async def test_a_long_but_weak_password_is_still_refused() -> None:
    with pytest.raises(WeakPasswordError) as refused:
        await validate_password("a" * 80, settings=_settings(password_breach_check_enabled=False))

    assert "too easy to guess" in refused.value.detail
