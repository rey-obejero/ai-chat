from http import HTTPStatus

from ai_chat.shared.exceptions import AppError


class LLMNotConfiguredError(AppError):
    """No provider credential is available for this request."""

    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "LLM_NOT_CONFIGURED"
    title = "LLM Not Configured"


class LLMProviderError(AppError):
    """The provider was reachable but failed to serve the request."""

    status_code = HTTPStatus.BAD_GATEWAY
    code = "LLM_PROVIDER_ERROR"
    title = "LLM Provider Error"
