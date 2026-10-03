"""SuperTokens wiring — the only module that imports the auth vendor.

Everything else depends on `ai_chat.auth.dependencies.get_current_user_id` and
`ai_chat.auth.port`, so the provider can be replaced in one place.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any
from urllib.parse import urlparse

from supertokens_python import InputAppInfo, SupertokensConfig, init
from supertokens_python.asyncio import get_user
from supertokens_python.framework import BaseRequest, BaseResponse
from supertokens_python.framework.fastapi import get_middleware
from supertokens_python.ingredients.emaildelivery.types import (
    EmailDeliveryConfig,
    EmailDeliveryInterface,
    SMTPSettings,
    SMTPSettingsFrom,
)
from supertokens_python.logger import log_debug_message
from supertokens_python.recipe import emailpassword, session, thirdparty
from supertokens_python.recipe.emailpassword import SMTPService
from supertokens_python.recipe.emailpassword.interfaces import (
    RecipeInterface,
    UpdateEmailOrPasswordOkResult,
)
from supertokens_python.recipe.emailpassword.types import EmailTemplateVars
from supertokens_python.recipe.emailpassword.utils import (
    EmailPasswordOverrideConfig,
)
from supertokens_python.recipe.session import InputErrorHandlers
from supertokens_python.recipe.session.asyncio import revoke_all_sessions_for_user
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
        ("google", "Google", settings.google_client_id, settings.google_client_secret),
        ("github", "GitHub", settings.github_client_id, settings.github_client_secret),
    ]
    for third_party_id, name, client_id, client_secret in candidates:
        if client_id and client_secret:
            providers.append(
                ProviderInput(
                    config=ProviderConfig(
                        third_party_id=third_party_id,
                        name=name,
                        clients=[
                            ProviderClientConfig(
                                client_id=client_id,
                                client_secret=client_secret,
                            )
                        ],
                    )
                )
            )

    test_provider = _test_provider(settings)
    if test_provider is not None:
        providers.append(test_provider)

    return providers


TEST_PROVIDER_ID = "test-idp"

# The only hosts the stand-in provider may live on. A real deployment cannot
# accidentally register an unverified identity provider by setting a flag and a
# URL, because a URL pointing anywhere else is refused.
TEST_PROVIDER_HOSTS = frozenset({"idp.test", "localhost", "127.0.0.1"})


def _test_provider(settings: Settings) -> ProviderInput | None:
    """The local identity provider the end-to-end suite runs (ADR-0029).

    Registered only when all three hold: an explicit switch, credentials, and a
    base URL on a known local host. Each is checked here rather than asserted in
    a comment, so the guard is the code.
    """
    if not settings.test_idp_enabled:
        return None
    if not settings.test_idp_base_url:
        return None
    if not (settings.test_idp_client_id and settings.test_idp_client_secret):
        return None

    host = urlparse(settings.test_idp_base_url).hostname
    if host not in TEST_PROVIDER_HOSTS:
        log_debug_message("test identity provider ignored: base URL host is not a test host")
        return None

    return ProviderInput(
        config=ProviderConfig(
            third_party_id=TEST_PROVIDER_ID,
            name="Test",
            # Discovery rather than the individual endpoints, so the spec
            # exercises the same path a real provider is configured with.
            oidc_discovery_endpoint=(
                f"{settings.test_idp_base_url.rstrip('/')}/.well-known/openid-configuration"
            ),
            clients=[
                ProviderClientConfig(
                    client_id=settings.test_idp_client_id,
                    client_secret=settings.test_idp_client_secret,
                )
            ],
        )
    )


def configured_providers(settings: Settings) -> list[tuple[str, str]]:
    """The (id, display name) pairs the core actually has credentials for.

    Derived from `_providers` rather than re-checking the credentials, so the
    UI and the core cannot disagree about which buttons exist.

    The name travels with the id so the front end does not keep its own copy of
    a label the backend already knows — the two would drift.
    """
    return [
        (provider.config.third_party_id, provider.config.name or provider.config.third_party_id)
        for provider in _providers(settings)
    ]


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


class MailNotConfiguredError(RuntimeError):
    """Raised when the reset flow needs to send mail but SMTP is unset."""


class _UnconfiguredEmailDelivery(EmailDeliveryInterface[EmailTemplateVars]):
    """Fails loudly where the SDK default fails silently.

    SuperTokens' default email delivery POSTs the reset link to SuperTokens'
    own service and swallows every error, so an unconfigured deployment answers
    a reset request with success and sends nothing. Raising here turns that
    invisible no-op into a server error someone can read.
    """

    async def send_email(
        self, template_vars: EmailTemplateVars, user_context: dict[str, Any]
    ) -> None:
        raise MailNotConfiguredError(
            "SMTP is not configured, so the password reset email cannot be "
            "sent. Set SMTP_HOST and SMTP_FROM_EMAIL (see .env.example)."
        )


def _email_delivery(settings: Settings) -> EmailDeliveryConfig[EmailTemplateVars]:
    """The email transport SuperTokens sends password-reset mail through.

    Configured over plain SMTP so the settings are provider-agnostic: Mailpit
    in development, Resend (or any SMTP host) in production.
    """
    if not settings.smtp_host or not settings.smtp_from_email:
        return EmailDeliveryConfig(service=_UnconfiguredEmailDelivery())

    return EmailDeliveryConfig(
        service=SMTPService(
            SMTPSettings(
                host=settings.smtp_host,
                port=settings.smtp_port,
                from_=SMTPSettingsFrom(
                    settings.smtp_from_name or settings.app_name,
                    settings.smtp_from_email,
                ),
                username=settings.smtp_username or None,
                password=settings.smtp_password or None,
                secure=settings.smtp_secure,
            )
        )
    )


def _app_info(settings: Settings) -> InputAppInfo:
    """The SuperTokens app identity. `website_base_path` is load-bearing: it is
    where the reset link points, so it must match the SPA's auth routes."""
    return InputAppInfo(
        app_name=settings.app_name,
        api_domain=settings.api_base_url,
        website_domain=settings.frontend_url,
        api_base_path="/api/auth",
        website_base_path="/authentication",
    )


async def revoke_all_sessions(user_id: str) -> None:
    """End every session for a user. The `UserDirectory` implementation."""
    await revoke_all_sessions_for_user(user_id)


def _revoke_sessions_on_password_change(original: RecipeInterface) -> RecipeInterface:
    """Revoke every session for a user whenever their password changes.

    The SDK consumes the reset token and updates the password but leaves
    existing sessions alive, so without this a reset does not evict someone who
    is already signed in — the exact thing a reset is for. This overrides the
    one function every password change goes through, and only acts on success.
    """
    original_update = original.update_email_or_password

    async def update_email_or_password(
        recipe_user_id,
        email,
        password,
        apply_password_policy,
        tenant_id_for_password_policy,
        user_context,
    ):
        result = await original_update(
            recipe_user_id=recipe_user_id,
            email=email,
            password=password,
            apply_password_policy=apply_password_policy,
            tenant_id_for_password_policy=tenant_id_for_password_policy,
            user_context=user_context,
        )
        if isinstance(result, UpdateEmailOrPasswordOkResult) and password is not None:
            await revoke_all_sessions(recipe_user_id.get_as_string())
        return result

    original.update_email_or_password = update_email_or_password
    return original


def init_supertokens(settings: Settings) -> None:
    init(
        app_info=_app_info(settings),
        supertokens_config=SupertokensConfig(
            connection_uri=settings.supertokens_connection_uri,
            api_key=settings.supertokens_api_key_or_none,
        ),
        framework="fastapi",
        recipe_list=[
            session.init(error_handlers=InputErrorHandlers(on_unauthorised=_on_unauthorised)),
            emailpassword.init(
                email_delivery=_email_delivery(settings),
                override=EmailPasswordOverrideConfig(functions=_revoke_sessions_on_password_change),
            ),
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
