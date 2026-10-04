from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ai_chat.auth.adapter_supertokens import get_email
from ai_chat.auth.models import User


async def get_or_create_user(session: AsyncSession, user_id: str) -> User:
    user = await session.get(User, user_id)
    if user is not None:
        return user

    user = User(id=user_id, email=await get_email(user_id))
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        # Two first requests for the same user can race and both try to insert.
        # The loser re-reads the row the winner committed instead of 500ing.
        # A *different* user with the same email is refused earlier, in the
        # social sign-in (ADR-0034), so it cannot reach here.
        await session.rollback()
        user = await session.get(User, user_id)
        if user is None:
            raise
        return user

    await session.refresh(user)
    return user
