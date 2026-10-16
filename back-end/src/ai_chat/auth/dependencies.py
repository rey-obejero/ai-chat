from fastapi import Depends
from supertokens_python.recipe.session import SessionContainer

from ai_chat.auth.adapter_supertokens import is_email_verified, session_dependency
from ai_chat.auth.exceptions import EmailNotVerifiedError


async def get_current_user_id(
    session: SessionContainer = Depends(session_dependency()),
) -> str:
    return session.get_user_id()


async def get_email_verified(
    user_id: str = Depends(get_current_user_id),
) -> bool:
    """Whether the caller's email address is verified (FR-4, ADR-0039).

    Read through the auth slice's short-lived cache, so a route that needs the
    answer costs no round trip per request; a failed lookup answers "unverified",
    because the reduced allowance must not open up while the auth service is
    unreachable.
    """
    return await is_email_verified(user_id)


async def require_verified_email(
    email_verified: bool = Depends(get_email_verified),
) -> None:
    """Gate a route on a verified address (ADR-0039, FR-4).

    For the routes that upload or retrieve, which are the ones an unverified
    account must not have; chat and reading stay open. Nothing is wired to this
    yet — the attachment routes (WI-9, WI-13) are where it lands.
    """
    if not email_verified:
        raise EmailNotVerifiedError("Verify your email address to use this feature.")
