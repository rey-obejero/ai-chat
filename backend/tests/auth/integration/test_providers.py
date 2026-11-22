from httpx import ASGITransport, AsyncClient

from ai_chat.shared.config import Settings
from conftest import _build_app


async def _providers(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get("/api/v1/auth/providers")


def _app(session_factory, **credentials):
    return _build_app(
        session_factory,
        Settings(
            _env_file=None,
            rate_limit_enabled=False,
            token_quota_enabled=False,
            **credentials,
        ),
    )


async def test_providers_is_empty_without_credentials(session_factory) -> None:
    # The default state of a fresh checkout: no OAuth apps registered, so the
    # social section hides entirely rather than offering buttons that fail.
    app = _app(session_factory)

    response = await _providers(app)

    assert response.status_code == 200
    assert response.json() == {"providers": []}


async def test_providers_lists_only_configured_ones(session_factory) -> None:
    # Half-configured counts as unconfigured: the core registers a provider
    # only when both halves are present, so the UI must agree.
    app = _app(
        session_factory,
        google_client_id="google-id",
        google_client_secret="google-secret",
        github_client_id="github-id",
    )

    response = await _providers(app)

    assert response.json() == {"providers": [{"id": "google", "name": "Google"}]}


async def test_providers_carry_a_display_name(session_factory) -> None:
    # The name travels with the id so the front end does not keep a second copy
    # of a label the backend already knows — the two would drift.
    app = _app(
        session_factory,
        google_client_id="id",
        google_client_secret="secret",
        github_client_id="id",
        github_client_secret="secret",
    )

    response = await _providers(app)

    assert response.json() == {
        "providers": [
            {"id": "google", "name": "Google"},
            {"id": "github", "name": "GitHub"},
        ]
    }


async def test_providers_is_public(session_factory) -> None:
    # The sign-in screen reads this before anyone has a session.
    app = _app(session_factory, google_client_id="id", google_client_secret="secret")

    response = await _providers(app)

    assert response.status_code == 200


async def test_providers_discloses_no_credentials(session_factory) -> None:
    app = _app(
        session_factory,
        google_client_id="client-id-value",
        google_client_secret="client-secret-value",
    )

    response = await _providers(app)

    assert "client-secret-value" not in response.text
    assert "client-id-value" not in response.text
