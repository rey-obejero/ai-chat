from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ai_chat.auth.adapter_supertokens import configured_providers
from ai_chat.auth.dependencies import get_current_user_id
from ai_chat.auth.schemas import (
    PreferencesUpdate,
    ProfileUpdate,
    SocialProviderRead,
    SocialProvidersRead,
    UserRead,
)
from ai_chat.auth.service import (
    get_or_create_user,
    mark_name_prompt_seen,
    update_display_name,
    update_preferences,
)
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


@router.patch("/me", response_model=UserRead)
async def update_me(
    payload: ProfileUpdate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    """Save the account's name, or record the skipped prompt (FR-7).

    Partial, like the preferences write: an absent field keeps its value. Saving
    a name answers the prompt, so the name wins when both arrive — a request
    naming itself and denying it answered is a contradiction, and the prompt's
    point is that it is answered once. The updated account comes back so the
    caller refreshes the prompt and the settings field from one response.
    """
    user = await get_or_create_user(session, user_id)
    if payload.display_name is not None:
        updated = await update_display_name(session, user, payload.display_name)
    elif payload.name_prompt_seen is not None:
        updated = await mark_name_prompt_seen(session, user, seen=payload.name_prompt_seen)
    else:
        # Nothing to change: still a read of the stored account, so `{}` is a
        # valid (if pointless) request rather than an error.
        updated = user
    return UserRead.model_validate(updated)


@router.put("/preferences", response_model=UserRead)
async def save_preferences(
    payload: PreferencesUpdate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    """Save the account's instructions and response style (FR-24, FR-25).

    Partial: a field that is absent keeps its value. The updated account comes
    back, so the caller can refresh the settings form and the greeting from one
    response rather than a second read.
    """
    user = await get_or_create_user(session, user_id)
    updated = await update_preferences(
        session,
        user,
        instructions=payload.instructions,
        response_style=payload.response_style,
    )
    return UserRead.model_validate(updated)


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
