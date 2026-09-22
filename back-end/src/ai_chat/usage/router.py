from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ai_chat.auth import get_current_user_id
from ai_chat.shared.config import Settings
from ai_chat.shared.db import get_session
from ai_chat.usage.schemas import UsageRead
from ai_chat.usage.service import period_bounds, spent_in_period

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("", response_model=UsageRead)
async def read_usage(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> UsageRead:
    settings: Settings = request.app.state.settings
    now = datetime.now(UTC)
    start, resets_at = period_bounds(now, settings.token_quota_period)
    used = await spent_in_period(session, user_id, period_start=start)

    limit = settings.token_quota_tokens if settings.token_quota_enabled else None
    remaining = max(0, limit - used) if limit is not None else None
    return UsageRead(
        used=used,
        limit=limit,
        remaining=remaining,
        period_start=start,
        resets_at=resets_at,
    )
