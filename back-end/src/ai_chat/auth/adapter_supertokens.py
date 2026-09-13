"""SuperTokens wiring — the only module that imports the auth vendor.

Everything else depends on `ai_chat.auth.dependencies.get_current_user_id` and
`ai_chat.auth.port`, so the provider can be replaced in one place.
"""

from __future__ import annotations

from http import HTTPStatus

from supertokens_python import InputAppInfo, SupertokensConfig, init
from supertokens_python.asyncio import get_user
from supertokens_python.framework import BaseRequest, BaseResponse
from supertokens_python.framework.fastapi import get_middleware
from supertokens_python.recipe import emailpassword, session, thirdparty
from supertokens_python.recipe.session import InputErrorHandlers
from supertokens_python.recipe.session.framework.fastapi import verify_session
from supertokens_python.recipe.thirdparty.provider import (
    ProviderClientConfig,
    ProviderConfig,
    ProviderInput,
)

from ai_chat.shared.config import Settings
from ai_chat.shared.exceptions import PROBLEM_JSON, problem_body

_PLACEHOLDER_EMAIL_DOMAIN = "unknown.local"


def _providers(settings: Settings) -> list[ProviderInput]:
    providers: list[ProviderInput] = []
    candidates = [
        ("google", settings.google_client_id, settings.google_client_secret),
        ("github", settings.github_client_id, settings.github_client_secret),
    ]
    for third_party_id, client_id, client_secret in candidates:
        if client_id and client_secret:
            providers.append(
                ProviderInput(
                    config=ProviderConfig(
                        third_party_id=third_party_id,
                        clients=[
                            ProviderClientConfig(
                                client_id=client_id,
                                client_secret=client_secret,
                            )
                        ],
                    )
                )
            )
    return providers


async def _on_unauthorised(
    request: BaseRequest, _message: str, response: BaseResponse
) -> BaseResponse:
    """Translate SuperTokens' session errors into the RFC 9457 envelope."""
    status_code = HTTPStatus.UNAUTHORIZED
    response.set_status_code(status_code)
    response.set_json_content(
        problem_body(
            status_code=status_code,
            title="Not Authenticated",
            detail="No active session.",
            code="NOT_AUTHENTICATED",
            instance=request.get_path(),
        )
    )
    response.set_header("Content-Type", PROBLEM_JSON)
    return response


def init_supertokens(settings: Settings) -> None:
    init(
        app_info=InputAppInfo(
            app_name=settings.app_name,
            api_domain=settings.api_base_url,
            website_domain=settings.frontend_url,
            api_base_path="/api/auth",
            website_base_path="/auth",
        ),
        supertokens_config=SupertokensConfig(
            connection_uri=settings.supertokens_connection_uri,
            api_key=settings.supertokens_api_key_or_none,
        ),
        framework="fastapi",
        recipe_list=[
            session.init(error_handlers=InputErrorHandlers(on_unauthorised=_on_unauthorised)),
            emailpassword.init(),
            thirdparty.init(
                sign_in_and_up_feature=thirdparty.SignInAndUpFeature(providers=_providers(settings))
            ),
        ],
    )


def supertokens_middleware():
    return get_middleware()


def session_dependency():
    return verify_session()


async def get_email(user_id: str) -> str:
    user = await get_user(user_id)
    if user is None or not user.emails:
        return f"{user_id}@{_PLACEHOLDER_EMAIL_DOMAIN}"
    return user.emails[0]
