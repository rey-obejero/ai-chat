from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ai_chat.auth.dependencies import get_current_user_id
from ai_chat.auth.schemas import UserRead
from ai_chat.auth.service import get_or_create_user
from ai_chat.shared.db import get_session

router = APIRouter(tags=["auth"])


@router.get("/me", response_model=UserRead)
async def read_me(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    user = await get_or_create_user(session, user_id)
    return UserRead.model_validate(user)
