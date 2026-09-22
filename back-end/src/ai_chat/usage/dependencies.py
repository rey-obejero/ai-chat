"""Route dependency that gates an expensive route on the token quota."""

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ai_chat.auth import get_current_user_id
from ai_chat.shared.config import Settings
from ai_chat.shared.db import get_session
from ai_chat.usage.service import enforce


async def enforce_quota(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Reject the request when the user is already over budget.

    A dependency rather than middleware (unlike the rate limit, ADR-0020): it
    runs after authentication and its domain exception reaches the normal
    problem+json handlers.
    """
    settings: Settings = request.app.state.settings
    await enforce(session, user_id, settings=settings)
