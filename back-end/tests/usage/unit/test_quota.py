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

        await service.enforce(session, "u1", settings=_settings(token_quota_tokens=100))


async def test_enforce_raises_at_the_budget(session_factory) -> None:
    async with session_factory() as session:
        await service.record(
            session, user_id="u1", conversation_id=None, usage=TokenUsage(total_tokens=100)
        )

        with pytest.raises(QuotaExceededError) as excinfo:
            await service.enforce(session, "u1", settings=_settings(token_quota_tokens=100))

    assert excinfo.value.code == "QUOTA_EXCEEDED"
    assert excinfo.value.extensions["retry_after"] >= 0


async def test_enforce_is_a_noop_when_the_quota_is_disabled(session_factory) -> None:
    async with session_factory() as session:
        await service.record(
            session, user_id="u1", conversation_id=None, usage=TokenUsage(total_tokens=10_000)
        )

        await service.enforce(
            session,
            "u1",
            settings=_settings(token_quota_enabled=False, token_quota_tokens=1),
        )
