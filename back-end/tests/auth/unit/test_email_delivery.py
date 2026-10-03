"""Email delivery selection and the reset link it produces (ADR-0030).

The SDK's default delivery silently reports success when mail is unconfigured,
so these tests pin down that this project refuses instead, and that the reset
link points at the SPA's auth route rather than the API.
"""

import pytest
from supertokens_python.recipe.emailpassword import SMTPService
from supertokens_python.recipe.emailpassword.utils import get_password_reset_link
from supertokens_python.supertokens import AppInfo

from ai_chat.auth.adapter_supertokens import (
    MailNotConfiguredError,
    _app_info,
    _email_delivery,
    _UnconfiguredEmailDelivery,
)
from ai_chat.shared.config import Settings


def _settings(**overrides) -> Settings:
    return Settings(_env_file=None, **overrides)


def test_mail_is_unconfigured_by_default() -> None:
    assert isinstance(_email_delivery(_settings()).service, _UnconfiguredEmailDelivery)


def test_a_host_without_a_sender_is_still_unconfigured() -> None:
    settings = _settings(smtp_host="mailpit")

    assert isinstance(_email_delivery(settings).service, _UnconfiguredEmailDelivery)


async def test_an_unconfigured_send_fails_loudly() -> None:
    # This is the whole point: the SDK default would answer the request with
    # success and send nothing.
    with pytest.raises(MailNotConfiguredError):
        await _UnconfiguredEmailDelivery().send_email(None, {})  # type: ignore[arg-type]


def test_configured_mail_uses_the_smtp_service() -> None:
    settings = _settings(
        smtp_host="mailpit",
        smtp_port=1025,
        smtp_from_email="no-reply@localhost",
    )

    assert isinstance(_email_delivery(settings).service, SMTPService)


def _reset_link(settings: Settings) -> str:
    info = _app_info(settings)
    app_info = AppInfo(
        app_name=info.app_name,
        api_domain=info.api_domain,
        website_domain=info.website_domain,
        framework="fastapi",
        api_gateway_path="",
        api_base_path=info.api_base_path,
        website_base_path=info.website_base_path,
        mode=None,
        origin=None,
    )
    return get_password_reset_link(
        app_info=app_info,
        token="tok",
        tenant_id="public",
        request=None,
        user_context={},
    )


def test_the_reset_link_targets_the_frontend_auth_route() -> None:
    settings = _settings(frontend_url="http://localhost:5173")

    link = _reset_link(settings)

    assert link == ("http://localhost:5173/authentication/reset-password?token=tok&tenantId=public")
