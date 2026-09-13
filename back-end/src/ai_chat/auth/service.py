from sqlalchemy.ext.asyncio import AsyncSession

from ai_chat.auth.adapter_supertokens import get_email
from ai_chat.auth.models import User


async def get_or_create_user(session: AsyncSession, user_id: str) -> User:
    user = await session.get(User, user_id)
    if user is not None:
        return user

    user = User(id=user_id, email=await get_email(user_id))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
