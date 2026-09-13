from ai_chat.auth import get_current_user_id
from ai_chat.auth.models import User
from ai_chat.shared.exceptions import NotAuthenticatedError


async def test_me_requires_session(app, client) -> None:
    async def unauthenticated() -> str:
        raise NotAuthenticatedError("No session cookie")

    app.dependency_overrides[get_current_user_id] = unauthenticated

    response = await client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "NOT_AUTHENTICATED"


async def test_me_returns_existing_user(app, client, session_factory) -> None:
    async def current_user() -> str:
        return "user-1"

    app.dependency_overrides[get_current_user_id] = current_user

    async with session_factory() as session:
        session.add(User(id="user-1", email="person@example.com"))
        await session.commit()

    response = await client.get("/api/v1/me")

    assert response.status_code == 200
    assert response.json()["id"] == "user-1"
    assert response.json()["email"] == "person@example.com"


async def test_me_creates_user_on_first_seen(app, client, monkeypatch) -> None:
    async def current_user() -> str:
        return "user-2"

    async def fake_email(_user_id: str) -> str:
        return "new@example.com"

    monkeypatch.setattr("ai_chat.auth.service.get_email", fake_email)
    app.dependency_overrides[get_current_user_id] = current_user

    response = await client.get("/api/v1/me")

    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"
