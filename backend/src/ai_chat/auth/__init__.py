from ai_chat.auth.dependencies import (
    get_current_user_id,
    get_email_verified,
    require_verified_email,
)
from ai_chat.auth.exceptions import EmailNotVerifiedError
from ai_chat.auth.identity import resolve_user_id
from ai_chat.auth.router import router
from ai_chat.auth.service import get_or_create_user

__all__ = [
    "EmailNotVerifiedError",
    "get_current_user_id",
    "get_email_verified",
    "get_or_create_user",
    "require_verified_email",
    "resolve_user_id",
    "router",
]
