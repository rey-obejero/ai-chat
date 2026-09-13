from ai_chat.shared.exceptions import AppError


class InvalidCredentialsError(AppError):
    status_code = 401
    code = "INVALID_CREDENTIALS"
    title = "Invalid Credentials"
