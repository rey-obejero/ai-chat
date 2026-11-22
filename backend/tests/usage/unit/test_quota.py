from datetime import UTC, datetime

import pytest

from ai_chat.llm import TokenUsage
from ai_chat.shared.config import Settings
from ai_chat.usage import service
from ai_chat.usage.exceptions import QuotaExceededError
from ai_chat.usage.models import TokenUsage as UsageRow


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)


def test_period_bounds_month() -> None:
    start, end = service.period_bounds(datetime(2026, 9, 22, 15, 30, tzinfo=UTC))

    assert start == datetime(2026, 9, 1, tzinfo=UTC)
    assert end == datetime(2026, 10, 1, tzinfo=UTC)


def test_period_bounds_month_rolls_over_the_year() -> None:
    start, end = service.period_bounds(datetime(2026, 12, 5, tzinfo=UTC))

    assert start == datetime(2026, 12, 1, tzinfo=UTC)
    assert end == datetime(2027, 1, 1, tzinfo=UTC)


def test_period_bounds_day() -> None:
    start, end = service.period_bounds(datetime(2026, 9, 22, 15, 30, tzinfo=UTC), "day")

    assert start == datetime(2026, 9, 22, tzinfo=UTC)
    assert end == datetime(2026, 9, 23, tzinfo=UTC)


def test_period_bounds_rejects_an_unknown_period() -> None:
    with pytest.raises(ValueError):
        service.period_bounds(datetime(2026, 9, 22, tzinfo=UTC), "week")


async def test_spent_in_period_counts_only_this_user_this_period(session_factory) -> None:
    async with session_factory() as session:
        session.add_all(
            [
                UsageRow(
                    user_id="u1", total_tokens=10, created_at=datetime(2026, 9, 10, tzinfo=UTC)
                ),
                UsageRow(
                    user_id="u1", total_tokens=5, created_at=datetime(2026, 8, 10, tzinfo=UTC)
                ),
                UsageRow(
                    user_id="u2", total_tokens=99, created_at=datetime(2026, 9, 10, tzinfo=UTC)
                ),
            ]
        )
        await session.commit()

        spent = await service.spent_in_period(
            session, "u1", period_start=datetime(2026, 9, 1, tzinfo=UTC)
        )

    assert spent == 10


async def test_enforce_allows_spend_under_the_budget(session_factory) -> None:
    async with session_factory() as session:
        await service.record(
            session, user_id="u1", conversation_id=None, usage=TokenUsage(total_tokens=99)
        )

        await service.enforce(
            session, "u1", email_verified=True, settings=_settings(token_quota_tokens=100)
        )


async def test_enforce_raises_at_the_budget(session_factory) -> None:
    async with session_factory() as session:
        await service.record(
            session, user_id="u1", conversation_id=None, usage=TokenUsage(total_tokens=100)
        )

        with pytest.raises(QuotaExceededError) as excinfo:
            await service.enforce(
                session, "u1", email_verified=True, settings=_settings(token_quota_tokens=100)
            )

    assert excinfo.value.code == "QUOTA_EXCEEDED"
    assert excinfo.value.extensions["retry_after"] >= 0
    # A verified account is never nudged to verify.
    assert "verification_required" not in excinfo.value.extensions


async def test_enforce_is_a_noop_when_the_quota_is_disabled(session_factory) -> None:
    async with session_factory() as session:
        await service.record(
            session, user_id="u1", conversation_id=None, usage=TokenUsage(total_tokens=10_000)
        )

        await service.enforce(
            session,
            "u1",
            # Disabled beats the split: there is no allowance to reduce.
            email_verified=False,
            settings=_settings(token_quota_enabled=False, token_quota_tokens=1),
        )


async def test_an_unverified_account_is_capped_at_half_the_quota(session_factory) -> None:
    settings = _settings(token_quota_tokens=1000)
    async with session_factory() as session:
        await service.record(
            session, user_id="u1", conversation_id=None, usage=TokenUsage(total_tokens=499)
        )
        await service.enforce(session, "u1", email_verified=False, settings=settings)

        await service.record(
            session, user_id="u1", conversation_id=None, usage=TokenUsage(total_tokens=1)
        )

        with pytest.raises(QuotaExceededError) as excinfo:
            await service.enforce(session, "u1", email_verified=False, settings=settings)

    # Half of 1000, and the refusal asks for the thing that would lift it.
    assert excinfo.value.extensions["verification_required"] is True


async def test_a_verified_account_spends_past_the_half_way_mark(session_factory) -> None:
    settings = _settings(token_quota_tokens=1000)
    async with session_factory() as session:
        await service.record(
            session, user_id="u1", conversation_id=None, usage=TokenUsage(total_tokens=500)
        )

        await service.enforce(session, "u1", email_verified=True, settings=settings)


async def test_the_unverified_allowance_can_be_set(session_factory) -> None:
    settings = _settings(token_quota_tokens=1000, token_quota_unverified_tokens=100)
    async with session_factory() as session:
        await service.record(
            session, user_id="u1", conversation_id=None, usage=TokenUsage(total_tokens=100)
        )

        with pytest.raises(QuotaExceededError):
            await service.enforce(session, "u1", email_verified=False, settings=settings)


def test_the_unverified_allowance_never_exceeds_the_full_one() -> None:
    # A pair of settings that disagree must not hand an unverified account more
    # than a verified one.
    settings = _settings(token_quota_tokens=1000, token_quota_unverified_tokens=5000)

    assert service.effective_limit(settings, email_verified=False) == 1000


def test_there_is_no_limit_when_the_quota_is_off() -> None:
    settings = _settings(token_quota_enabled=False)

    assert service.effective_limit(settings, email_verified=False) is None
    assert service.effective_limit(settings, email_verified=True) is None
