from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ai_chat.auth import get_current_user_id, get_email_verified
from ai_chat.shared.config import Settings
from ai_chat.shared.db import get_session
from ai_chat.usage.schemas import UsageRead
from ai_chat.usage.service import effective_limit, period_bounds, spent_in_period

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("", response_model=UsageRead)
async def read_usage(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
    email_verified: bool = Depends(get_email_verified),
) -> UsageRead:
    """The account's spend, measured against its own allowance (FR-4).

    An unverified account's allowance is the reduced one (ADR-0039), so this
    reports what the next reply is actually checked against rather than the
    full quota it would be refused under.
    """
    settings: Settings = request.app.state.settings
    now = datetime.now(UTC)
    start, resets_at = period_bounds(now, settings.token_quota_period)
    used = await spent_in_period(session, user_id, period_start=start)

    limit = effective_limit(settings, email_verified=email_verified)
    remaining = max(0, limit - used) if limit is not None else None
    return UsageRead(
        used=used,
        limit=limit,
        # What a verified account gets, so a reduced limit can be explained
        # rather than merely reported (FR-4).
        full_limit=settings.token_quota_tokens if limit is not None else None,
        remaining=remaining,
        period_start=start,
        resets_at=resets_at,
    )
