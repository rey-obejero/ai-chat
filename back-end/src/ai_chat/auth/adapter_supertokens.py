"""SuperTokens wiring — the only module that imports the auth vendor.

Everything else depends on `ai_chat.auth.dependencies.get_current_user_id` and
`ai_chat.auth.port`, so the provider can be replaced in one place.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from http import HTTPStatus
from typing import Any, TypeVar
from urllib.parse import urlparse

from supertokens_python import InputAppInfo, SupertokensConfig, init
from supertokens_python.asyncio import get_user, list_users_by_account_info
from supertokens_python.framework import BaseRequest, BaseResponse
from supertokens_python.framework.fastapi import get_middleware
from supertokens_python.ingredients.emaildelivery.types import (
    EmailDeliveryConfig,
    EmailDeliveryInterface,
    SMTPSettings,
    SMTPSettingsFrom,
)
from supertokens_python.logger import log_debug_message
from supertokens_python.recipe import emailpassword, emailverification, session, thirdparty
from supertokens_python.recipe.emailpassword import SMTPService
from supertokens_python.recipe.emailpassword.exceptions import raise_form_field_exception
from supertokens_python.recipe.emailpassword.interfaces import (
    RecipeInterface,
    SignUpOkResult,
    UpdateEmailOrPasswordOkResult,
)
from supertokens_python.recipe.emailpassword.types import (
    EmailTemplateVars,
    ErrorFormField,
)
from supertokens_python.recipe.emailpassword.utils import (
    EmailPasswordOverrideConfig,
)
from supertokens_python.recipe.emailverification import (
    SMTPService as VerificationSMTPService,
)
from supertokens_python.recipe.emailverification.asyncio import (
    is_email_verified as read_verification_state,
)
from supertokens_python.recipe.emailverification.asyncio import (
    send_email_verification_email,
)
from supertokens_python.recipe.emailverification.interfaces import (
    RecipeInterface as EmailVerificationRecipeInterface,
)
from supertokens_python.recipe.emailverification.interfaces import (
    VerifyEmailUsingTokenOkResult,
)
from supertokens_python.recipe.emailverification.types import (
    VerificationEmailTemplateVars,
)
from supertokens_python.recipe.emailverification.utils import (
    EmailVerificationOverrideConfig,
)
from supertokens_python.recipe.session import InputErrorHandlers
from supertokens_python.recipe.session.asyncio import revoke_all_sessions_for_user
from supertokens_python.recipe.session.framework.fastapi import verify_session
from supertokens_python.recipe.thirdparty.interfaces import (
    RecipeInterface as ThirdPartyRecipeInterface,
)
from supertokens_python.recipe.thirdparty.interfaces import (
    SignInUpNotAllowed,
)
from supertokens_python.recipe.thirdparty.provider import (
    ProviderClientConfig,
    ProviderConfig,
    ProviderInput,
)
from supertokens_python.types import RecipeUserId
from supertokens_python.types.base import AccountInfoInput

from ai_chat.auth.exceptions import WeakPasswordError
from ai_chat.auth.passwords import validate_password
from ai_chat.auth.verification import VerificationStateCache
from ai_chat.shared.config import Settings
from ai_chat.shared.exceptions import PROBLEM_JSON, problem_body

logger = logging.getLogger(__name__)

_PLACEHOLDER_EMAIL_DOMAIN = "unknown.local"

# The email delivery types are parameterized by template vars, and one
# unconfigured-delivery class serves both recipes.
_TemplateVars = TypeVar("_TemplateVars")


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


class _UnconfiguredEmailDelivery(EmailDeliveryInterface[_TemplateVars]):
    """Fails loudly where the SDK default fails silently.

    SuperTokens' default email delivery POSTs the message to SuperTokens' own
    service and swallows every error, so an unconfigured deployment answers a
    reset request with success and sends nothing. Raising here turns that
    invisible no-op into an error someone can read (ADR-0030).
    """

    async def send_email(self, template_vars: _TemplateVars, user_context: dict[str, Any]) -> None:
        raise MailNotConfiguredError(
            "SMTP is not configured, so mail cannot be sent. Set SMTP_HOST and "
            "SMTP_FROM_EMAIL (see .env.example)."
        )


def _smtp_settings(settings: Settings) -> SMTPSettings:
    """The plain-SMTP transport both mail senders share (ADR-0030)."""
    return SMTPSettings(
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


def _email_delivery(settings: Settings) -> EmailDeliveryConfig[EmailTemplateVars]:
    """The email transport SuperTokens sends password-reset mail through.

    Configured over plain SMTP so the settings are provider-agnostic: Mailpit
    in development, Resend (or any SMTP host) in production.
    """
    if not settings.smtp_host or not settings.smtp_from_email:
        return EmailDeliveryConfig(service=_UnconfiguredEmailDelivery())

    return EmailDeliveryConfig(service=SMTPService(_smtp_settings(settings)))


def _verification_email_delivery(
    settings: Settings,
) -> EmailDeliveryConfig[VerificationEmailTemplateVars]:
    """The transport verification mail goes out through (FR-4).

    The same SMTP settings as the reset mail — one transport, two templates,
    both owned by the SDK. The verify link it builds points at
    `frontend_url` + `/authentication/verify-email`, which is the SPA's route.

    Unconfigured, this is the raising delivery: a resend that reports success
    while sending nothing is the failure ADR-0030 exists to prevent. The
    sign-up path catches that on the way out, because by then the account
    exists and mail must not turn a created account into an error.
    """
    if not settings.smtp_host or not settings.smtp_from_email:
        return EmailDeliveryConfig(service=_UnconfiguredEmailDelivery())

    return EmailDeliveryConfig(service=VerificationSMTPService(_smtp_settings(settings)))


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


async def _screen(password: str, settings: Settings) -> None:
    """Refuse a password the screening rejects, as a field error with the reason.

    The SDK serializes the raised error as a response whose body is
    `{"status": "FIELD_ERROR", "formFields": [{"id": "password", "error": …}]}`,
    which is the shape the sign-up and reset forms already render per field —
    and the same one the core's own password policy would produce.
    """
    try:
        await validate_password(password, settings=settings)
    except WeakPasswordError as error:
        # `raise_form_field_exception` raises the SDK's `FieldError` for us;
        # the reason travels in the field, not in the exception chain.
        raise_form_field_exception(
            "Error in input formFields",
            [ErrorFormField(id="password", error=error.detail)],
        )


async def _send_verification_email(
    sign_up: SignUpOkResult, email: str, tenant_id: str, user_context: dict[str, Any]
) -> None:
    """Send the verification mail for the account that has just been created.

    Sent here rather than left to the client to ask for: FR-4 says the mail goes
    out shortly after sign-up, and this is the moment the app knows an account
    is new. A failure is logged, not raised — the account exists either way, so
    a mail problem must not turn a successful sign-up into an error. The resend
    endpoint is the remedy, and there the failure *is* the response.
    """
    try:
        await send_email_verification_email(
            tenant_id=tenant_id,
            user_id=sign_up.user.id,
            recipe_user_id=sign_up.recipe_user_id,
            email=email,
            user_context=user_context,
        )
    except Exception:
        logger.warning("Verification email could not be sent after sign-up", exc_info=True)


def _screen_passwords(settings: Settings) -> Callable[[RecipeInterface], RecipeInterface]:
    """Build the password-screening override for a deployment's settings.

    It takes the settings rather than reading the process-wide ones, so the
    validator's thresholds, the breach check's switch, and the breach check's
    timeout are the app's configuration — including for a test that builds an app
    with its own.

    This covers both ways a password is chosen: sign-up, and the update that the
    reset flow goes through. The check runs *before* the original function, so a
    rejected password never reaches the core and no account is created for it
    (FR-2, ADR-0038).
    """

    def override(original: RecipeInterface) -> RecipeInterface:
        original_sign_up = original.sign_up
        original_update = original.update_email_or_password

        async def sign_up(
            email,
            password,
            tenant_id,
            session,
            should_try_linking_with_session_user,
            user_context,
        ):
            await _screen(password, settings)
            result = await original_sign_up(
                email=email,
                password=password,
                tenant_id=tenant_id,
                session=session,
                should_try_linking_with_session_user=should_try_linking_with_session_user,
                user_context=user_context,
            )
            if isinstance(result, SignUpOkResult):
                await _send_verification_email(result, email, tenant_id, user_context)
            return result

        async def update_email_or_password(
            recipe_user_id,
            email,
            password,
            apply_password_policy,
            tenant_id_for_password_policy,
            user_context,
        ):
            # `None` is the email-only change; there is no password to screen.
            if password is not None:
                await _screen(password, settings)
            return await original_update(
                recipe_user_id=recipe_user_id,
                email=email,
                password=password,
                apply_password_policy=apply_password_policy,
                tenant_id_for_password_policy=tenant_id_for_password_policy,
                user_context=user_context,
            )

        original.sign_up = sign_up
        original.update_email_or_password = update_email_or_password
        return original

    return override


async def _read_email_verified(user_id: str) -> bool:
    """Ask the auth service whether the account's email is verified.

    Account ids and recipe user ids are the same for the accounts this app
    creates: one login method per account, because linking is refused
    (ADR-0028).
    """
    return bool(await read_verification_state(RecipeUserId(user_id)))


_verification_state = VerificationStateCache(_read_email_verified)


async def is_email_verified(user_id: str) -> bool:
    """Whether the account's email address is verified (FR-4, ADR-0039)."""
    return await _verification_state.is_verified(user_id)


def forget_email_verified(user_id: str) -> None:
    """Drop cached state for an account whose verification just changed."""
    _verification_state.forget(user_id)


def _forget_cached_verification_state(
    original: EmailVerificationRecipeInterface,
) -> EmailVerificationRecipeInterface:
    """Make a successful verification visible at once, not after the cache TTL.

    The cache in front of the read is short-lived rather than instantaneous, and
    only the TTL bounds how long a just-verified account still sees the reduced
    allowance. This closes that gap for the account that just verified — which
    is the one account the delay is visible to.
    """
    original_verify = original.verify_email_using_token

    async def verify_email_using_token(token, tenant_id, attempt_account_linking, user_context):
        result = await original_verify(token, tenant_id, attempt_account_linking, user_context)
        if isinstance(result, VerifyEmailUsingTokenOkResult):
            forget_email_verified(result.user.recipe_user_id.get_as_string())
        return result

    original.verify_email_using_token = verify_email_using_token
    return original


def _refuse_sign_in_when_email_exists(
    original: ThirdPartyRecipeInterface,
) -> ThirdPartyRecipeInterface:
    """Refuse a social sign-in whose email already belongs to another account.

    ADR-0028 requires identities to be neither merged nor duplicated. The SDK's
    default account linking does not do this: a verified email is allowed
    through, and a *second* account is created for it, which then collides with
    the app's unique email constraint. So the rule is enforced here, at the one
    function every provider funnels through. Returning `SignInUpNotAllowed`
    surfaces as the front end's existing-account message.

    A returning social user is allowed: their own login method matches the
    third-party identity, and there is no other account to conflict with.
    """
    original_sign_in_up = original.sign_in_up

    async def sign_in_up(
        third_party_id,
        third_party_user_id,
        email,
        is_verified,
        oauth_tokens,
        raw_user_info_from_provider,
        session,
        should_try_linking_with_session_user,
        tenant_id,
        user_context,
    ):
        existing = await list_users_by_account_info(
            tenant_id,
            AccountInfoInput(email=email),
            do_union_of_account_info=True,
            user_context=user_context,
        )
        same_identity = any(
            login.recipe_id == "thirdparty"
            and login.third_party is not None
            and login.third_party.id == third_party_id
            and login.third_party.user_id == third_party_user_id
            for user in existing
            for login in user.login_methods
        )
        if existing and not same_identity:
            return SignInUpNotAllowed(
                reason=(
                    "This email already has an account. Sign in with the method "
                    "you originally used."
                )
            )

        return await original_sign_in_up(
            third_party_id=third_party_id,
            third_party_user_id=third_party_user_id,
            email=email,
            is_verified=is_verified,
            oauth_tokens=oauth_tokens,
            raw_user_info_from_provider=raw_user_info_from_provider,
            session=session,
            should_try_linking_with_session_user=should_try_linking_with_session_user,
            tenant_id=tenant_id,
            user_context=user_context,
        )

    original.sign_in_up = sign_in_up
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
                override=EmailPasswordOverrideConfig(
                    # Both overrides wrap the same functions, so they compose by
                    # wrapping in turn rather than replacing each other:
                    # screening is innermost, so a password it refuses never
                    # reaches the SDK's own policy or the core, and the session
                    # revocation is outermost, so it acts on a change that
                    # happened.
                    functions=lambda original: _revoke_sessions_on_password_change(
                        _screen_passwords(settings)(original)
                    ),
                ),
            ),
            # Verification is a soft nudge, never a gate (ADR-0039), so the
            # recipe runs in OPTIONAL mode and the reduced allowance is the
            # incentive. In REQUIRED mode the SDK would block other endpoints
            # before this app's handlers ever see the request.
            emailverification.init(
                mode="OPTIONAL",
                email_delivery=_verification_email_delivery(settings),
                override=EmailVerificationOverrideConfig(
                    functions=_forget_cached_verification_state
                ),
            ),
            thirdparty.init(
                sign_in_and_up_feature=thirdparty.SignInAndUpFeature(
                    providers=_providers(settings)
                ),
                override=thirdparty.ThirdPartyOverrideConfig(
                    functions=_refuse_sign_in_when_email_exists
                ),
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
