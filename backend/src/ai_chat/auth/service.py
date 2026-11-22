from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ai_chat.auth.adapter_supertokens import get_email
from ai_chat.auth.display_name import derive_display_name, validate_display_name
from ai_chat.auth.models import User
from ai_chat.llm import ResponseStyle


async def get_or_create_user(session: AsyncSession, user_id: str) -> User:
    user = await session.get(User, user_id)
    if user is not None:
        return user

    # The name exists from creation (FR-7, decision 1). Social sign-in takes the
    # same path — the derivation reads the email, never the provider's name
    # (ADR-0045).
    email = await get_email(user_id)
    user = User(id=user_id, email=email, display_name=derive_display_name(email))
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


async def update_display_name(session: AsyncSession, user: User, display_name: str) -> User:
    """Save the account's name (FR-7).

    Saving a name is an answer to the first-run prompt, so the flag follows it:
    the prompt is asked once, and naming yourself is the account answering it.
    The rule lives in the domain module and refuses with the reason the field and
    the prompt both show; the stored value is the checked one.
    """
    user.display_name = validate_display_name(display_name)
    user.name_prompt_seen = True
    await session.commit()
    await session.refresh(user)
    return user


async def mark_name_prompt_seen(session: AsyncSession, user: User, *, seen: bool = True) -> User:
    """Record the first-run prompt's outcome (FR-7).

    Skipping is this call: the flag is the answer, and the derived name stands
    until the account chooses another one. `seen=False` re-opens the prompt;
    nothing in the product asks for that yet, but the flag is the account's own
    boolean rather than a one-way latch.
    """
    user.name_prompt_seen = seen
    await session.commit()
    await session.refresh(user)
    return user
