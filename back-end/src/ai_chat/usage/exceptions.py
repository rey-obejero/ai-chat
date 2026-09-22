from http import HTTPStatus

from ai_chat.shared.exceptions import AppError


class QuotaExceededError(AppError):
    """The user has spent their token budget for the current period."""

    status_code = HTTPStatus.TOO_MANY_REQUESTS
    code = "QUOTA_EXCEEDED"
    title = "Token Quota Exceeded"
