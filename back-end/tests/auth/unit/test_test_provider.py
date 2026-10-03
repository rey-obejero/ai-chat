"""The gate on the stand-in identity provider (ADR-0029).

Each condition is exercised on its own, because the guard is the only thing
standing between a stray environment variable and an unverified identity
provider in front of real users.
"""

from ai_chat.auth.adapter_supertokens import (
    TEST_PROVIDER_ID,
    _test_provider,
    configured_providers,
)
from ai_chat.shared.config import Settings


def _settings(**overrides) -> Settings:
    return Settings(_env_file=None, **overrides)


FULLY_CONFIGURED = {
    "test_idp_enabled": True,
    "test_idp_base_url": "http://idp.test:4011",
    "test_idp_client_id": "client",
    "test_idp_client_secret": "secret",
}


def test_absent_by_default() -> None:
    assert _test_provider(_settings()) is None


def test_credentials_alone_are_not_enough() -> None:
    # The switch has to be set explicitly. This is the case that would otherwise
    # turn it on by accident, since a test run exports the other two.
    settings = _settings(**{**FULLY_CONFIGURED, "test_idp_enabled": False})

    assert _test_provider(settings) is None


def test_the_switch_alone_is_not_enough() -> None:
    settings = _settings(test_idp_enabled=True)

    assert _test_provider(settings) is None


def test_half_a_credential_pair_is_not_enough() -> None:
    settings = _settings(**{**FULLY_CONFIGURED, "test_idp_client_secret": ""})

    assert _test_provider(settings) is None


def test_a_real_host_is_refused() -> None:
    # The point of the host check: setting the switch and a URL that points at a
    # real provider must not register an unverified one.
    settings = _settings(
        **{**FULLY_CONFIGURED, "test_idp_base_url": "https://accounts.example.com"}
    )

    assert _test_provider(settings) is None


def test_registered_when_every_condition_holds() -> None:
    provider = _test_provider(_settings(**FULLY_CONFIGURED))

    assert provider is not None
    assert provider.config.third_party_id == TEST_PROVIDER_ID
    assert provider.config.oidc_discovery_endpoint == (
        "http://idp.test:4011/.well-known/openid-configuration"
    )


def test_reaches_the_provider_list_when_enabled() -> None:
    # It is registered through the same path as the real providers, so the UI
    # and the core cannot disagree about which buttons exist.
    providers = configured_providers(_settings(**FULLY_CONFIGURED))

    assert (TEST_PROVIDER_ID, "Test") in providers


def test_absent_from_the_provider_list_by_default() -> None:
    providers = configured_providers(
        _settings(test_idp_base_url="http://idp.test:4011", test_idp_client_id="c")
    )

    assert all(provider_id != TEST_PROVIDER_ID for provider_id, _ in providers)
