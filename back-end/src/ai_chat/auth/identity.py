"""Identity resolution for middleware.

Route handlers depend on ``get_current_user_id``; middleware runs before
dependencies, so it needs its own entry point into the same session. Kept in
``auth`` so the vendor stays behind one boundary (ADR-0010).
"""

from __future__ import annotations

from starlette.requests import Request
from supertokens_python.recipe.session.framework.fastapi import verify_session

# Anti-CSRF is irrelevant when only reading identity, and an absent session is
# not an error: anonymous callers fall back to IP-based limiting.
_optional_session = verify_session(session_required=False, anti_csrf_check=False)


async def resolve_user_id(request: Request) -> str | None:
    """Return the session's user id, or ``None`` when unauthenticated.

    Best-effort by design. The caller is a rate limiter that fails open, so any
    session failure — an access token awaiting refresh, or a recipe that is not
    initialised in tests — degrades to anonymous instead of raising.
    """
    try:
        session = await _optional_session(request)
    except Exception:
        return None
    return session.get_user_id() if session is not None else None
