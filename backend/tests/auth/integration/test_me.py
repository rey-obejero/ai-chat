from ai_chat.auth import get_current_user_id, get_email_verified
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


def _email_verified(app, *, verified: bool) -> None:
    async def override() -> bool:
        return verified

    app.dependency_overrides[get_email_verified] = override


async def test_me_reports_an_unverified_address(app, client, session_factory) -> None:
    # No override, and no auth service answering in this process: the read fails
    # and the answer is the conservative one (ADR-0039) — an account nobody has
    # proved anything about is not verified.
    async def current_user() -> str:
        return "user-3"

    app.dependency_overrides[get_current_user_id] = current_user
    async with session_factory() as session:
        session.add(User(id="user-3", email="person@example.com"))
        await session.commit()

    response = await client.get("/api/v1/me")

    assert response.status_code == 200
    assert response.json()["email_verified"] is False


async def test_me_reports_a_verified_address(app, client, session_factory) -> None:
    async def current_user() -> str:
        return "user-4"

    app.dependency_overrides[get_current_user_id] = current_user
    _email_verified(app, verified=True)
    async with session_factory() as session:
        session.add(User(id="user-4", email="person@example.com"))
        await session.commit()

    response = await client.get("/api/v1/me")

    assert response.status_code == 200
    assert response.json()["email_verified"] is True
