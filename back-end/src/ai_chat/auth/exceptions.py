from http import HTTPStatus

from ai_chat.shared.exceptions import AppError


class InvalidCredentialsError(AppError):
    status_code = 401
    code = "INVALID_CREDENTIALS"
    title = "Invalid Credentials"


class WeakPasswordError(AppError):
    """The submitted password failed screening (FR-2, ADR-0038).

    The detail is the readable reason the form shows: SuperTokens' `sign_up` and
    password-reset overrides turn it into a field error on the password field,
    so the reason reaches the user rather than a generic refusal.
    """

    status_code = HTTPStatus.BAD_REQUEST
    code = "WEAK_PASSWORD"
    title = "Weak Password"


class EmailNotVerifiedError(AppError):
    """The account's address is not verified and the route requires it (FR-4).

    Verification never blocks sign-in or reading (ADR-0039); this is only for
    the routes that do upload or retrieve at a cost, which gate themselves on
    `require_verified_email`.
    """

    status_code = HTTPStatus.FORBIDDEN
    code = "EMAIL_NOT_VERIFIED"
    title = "Email Not Verified"
