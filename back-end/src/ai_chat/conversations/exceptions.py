from http import HTTPStatus

from ai_chat.shared.exceptions import AppError


class InvalidCursorError(AppError):
    """The list cursor is not one this service minted."""

    status_code = HTTPStatus.BAD_REQUEST
    code = "INVALID_CURSOR"
    title = "Invalid Cursor"
