from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ai_chat.auth.adapter_supertokens import get_email
from ai_chat.auth.models import User
from ai_chat.llm import ResponseStyle


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


async def update_preferences(
    session: AsyncSession,
    user: User,
    *,
    instructions: str | None = None,
    response_style: ResponseStyle | None = None,
) -> User:
    """Apply a partial update of the account's personalisation (FR-24, FR-25).

    ``None`` means "leave this field alone", so the schema's trimming decides
    what an empty instruction means: clearing it. The column is nullable, and
    "no instructions" has one representation, not two.
    """
    if instructions is not None:
        user.instructions = instructions or None
    if response_style is not None:
        user.response_style = str(response_style)
    await session.commit()
    await session.refresh(user)
    return user
