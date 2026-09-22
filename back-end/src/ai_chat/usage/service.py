"""Token accounting and the per-user quota (ADR-0024).

The request-rate limit (ADR-0020) bounds how often a user may call; this bounds
how much they may spend, which a rate limit cannot do on its own.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_chat.llm import TokenUsage as TokenCount
from ai_chat.shared.config import Settings, get_settings
from ai_chat.usage.exceptions import QuotaExceededError
from ai_chat.usage.models import TokenUsage


def period_bounds(now: datetime, period: str = "month") -> tuple[datetime, datetime]:
    """The period containing ``now``, as a half-open ``[start, next_start)``."""
    if period == "day":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, start + timedelta(days=1)

    if period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start.month == 12:
            next_start = start.replace(year=start.year + 1, month=1)
        else:
            next_start = start.replace(month=start.month + 1)
        return start, next_start

    raise ValueError(f"Unsupported token quota period: {period!r}")


async def record(
    session: AsyncSession,
    *,
    user_id: str,
    conversation_id: uuid.UUID | None,
    usage: TokenCount,
) -> None:
    """Append one completed reply's token spend to the ledger."""
    session.add(
        TokenUsage(
            user_id=user_id,
            conversation_id=conversation_id,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
        )
    )
    await session.commit()


async def spent_in_period(session: AsyncSession, user_id: str, *, period_start: datetime) -> int:
    """Total tokens this user has spent since ``period_start``."""
    result = await session.execute(
        select(func.coalesce(func.sum(TokenUsage.total_tokens), 0)).where(
            TokenUsage.user_id == user_id,
            TokenUsage.created_at >= period_start,
        )
    )
    return int(result.scalar_one())


async def enforce(
    session: AsyncSession,
    user_id: str,
    *,
    settings: Settings | None = None,
    now: datetime | None = None,
) -> None:
    """Raise ``QuotaExceededError`` once the period budget is spent.

    Checked before a reply starts, not reserved per request: a user can exceed
    the budget by at most one reply, and the provider-side spend cap is the hard
    backstop (ADR-0019).
    """
    settings = settings or get_settings()
    if not settings.token_quota_enabled:
        return

    now = now or datetime.now(UTC)
    start, resets_at = period_bounds(now, settings.token_quota_period)
    used = await spent_in_period(session, user_id, period_start=start)
    if used < settings.token_quota_tokens:
        return

    retry_after = max(0, int((resets_at - now).total_seconds()))
    raise QuotaExceededError(
        detail="You have used your token quota for this period.",
        extensions={"retry_after": retry_after},
    )
