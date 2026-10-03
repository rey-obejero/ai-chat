from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ai_chat.auth.adapter_supertokens import configured_providers
from ai_chat.auth.dependencies import get_current_user_id
from ai_chat.auth.schemas import SocialProviderRead, SocialProvidersRead, UserRead
from ai_chat.auth.service import get_or_create_user
from ai_chat.shared.config import Settings
from ai_chat.shared.db import get_session

router = APIRouter(tags=["auth"])


@router.get("/me", response_model=UserRead)
async def read_me(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    user = await get_or_create_user(session, user_id)
    return UserRead.model_validate(user)


@router.get("/auth/providers", response_model=SocialProvidersRead)
async def list_social_providers(request: Request) -> SocialProvidersRead:
    """The social providers this deployment has credentials for.

    Unauthenticated by necessity: the sign-in screen reads it before anyone has
    a session. Providers are configured per deployment, so a hardcoded button
    list is wrong in at least one environment at any time (ADR-0010).
    """
    settings: Settings = request.app.state.settings
    return SocialProvidersRead(
        providers=[
            # The name is the backend's, and the button wording is the front
            # end's; keeping them apart stops a label being defined twice.
            SocialProviderRead(id=provider_id, name=name)
            for provider_id, name in configured_providers(settings)
        ]
    )
