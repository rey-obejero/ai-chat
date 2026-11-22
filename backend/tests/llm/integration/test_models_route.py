"""The served model list the picker reads (FR-23)."""

from ai_chat.auth import get_current_user_id
from ai_chat.shared.exceptions import NotAuthenticatedError


def _current_user(app, user_id: str = "user-1") -> None:
    async def override() -> str:
        return user_id

    app.dependency_overrides[get_current_user_id] = override


async def test_the_list_needs_a_session(app, client) -> None:
    async def unauthenticated() -> str:
        raise NotAuthenticatedError("No session cookie")

    app.dependency_overrides[get_current_user_id] = unauthenticated

    response = await client.get("/api/v1/models")

    assert response.status_code == 401
    assert response.json()["code"] == "NOT_AUTHENTICATED"


async def test_a_deployment_without_a_list_serves_its_one_model(app, client) -> None:
    _current_user(app)

    response = await client.get("/api/v1/models")

    assert response.status_code == 200
    assert response.json() == [
        {"id": "openai/gpt-4o-mini", "label": "openai/gpt-4o-mini", "is_default": True}
    ]


async def test_the_configured_models_are_served_with_one_default(
    two_model_app, two_model_client
) -> None:
    _current_user(two_model_app)

    response = await two_model_client.get("/api/v1/models")

    assert response.status_code == 200
    assert response.json() == [
        {"id": "openai/gpt-4o-mini", "label": "openai/gpt-4o-mini", "is_default": True},
        {"id": "anthropic/claude-haiku", "label": "anthropic/claude-haiku", "is_default": False},
    ]
