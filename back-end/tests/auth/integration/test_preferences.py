"""Saving the account's instructions and response style (FR-24, FR-25)."""

from ai_chat.auth import get_current_user_id
from ai_chat.auth.models import User

OWNER = "user-1"
OTHER = "user-2"


def _current_user(app, user_id: str = OWNER) -> None:
    async def override() -> str:
        return user_id

    app.dependency_overrides[get_current_user_id] = override


async def _seed_user(session_factory, user_id: str = OWNER) -> None:
    async with session_factory() as session:
        session.add(User(id=user_id, email=f"{user_id}@example.com"))
        await session.commit()


async def test_a_new_account_has_no_instructions_and_the_default_style(
    app, client, session_factory
) -> None:
    _current_user(app)
    await _seed_user(session_factory)

    response = await client.get("/api/v1/me")

    assert response.status_code == 200
    assert response.json()["instructions"] is None
    assert response.json()["response_style"] == "default"


async def test_saving_returns_the_stored_account(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_user(session_factory)

    response = await client.put(
        "/api/v1/preferences",
        json={"instructions": "  Answer in metric units.  ", "response_style": "concise"},
    )

    assert response.status_code == 200, response.text
    saved = response.json()
    assert saved["instructions"] == "Answer in metric units."
    assert saved["response_style"] == "concise"
    # The settings form and any greeting read the same stored value.
    assert (await client.get("/api/v1/me")).json() == saved


async def test_each_field_is_saved_on_its_own(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_user(session_factory)
    await client.put("/api/v1/preferences", json={"instructions": "Be brief."})

    response = await client.put("/api/v1/preferences", json={"response_style": "formal"})

    assert response.status_code == 200, response.text
    assert response.json()["instructions"] == "Be brief."
    assert response.json()["response_style"] == "formal"


async def test_an_empty_save_changes_nothing(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_user(session_factory)
    await client.put("/api/v1/preferences", json={"instructions": "Be brief."})

    response = await client.put("/api/v1/preferences", json={})

    assert response.status_code == 200
    assert response.json()["instructions"] == "Be brief."


async def test_instructions_over_the_cap_are_refused(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_user(session_factory)

    response = await client.put("/api/v1/preferences", json={"instructions": "x" * 2001})

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert (await client.get("/api/v1/me")).json()["instructions"] is None


async def test_the_cap_is_measured_after_trimming(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_user(session_factory)

    response = await client.put("/api/v1/preferences", json={"instructions": f"  {'x' * 2000}  "})

    assert response.status_code == 200, response.text
    assert len(response.json()["instructions"]) == 2000


async def test_an_unknown_style_is_refused(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_user(session_factory)

    response = await client.put("/api/v1/preferences", json={"response_style": "poetic"})

    assert response.status_code == 422
    errors = response.json()["errors"]
    assert any(error["location"][-1] == "response_style" for error in errors)
    assert (await client.get("/api/v1/me")).json()["response_style"] == "default"


async def test_clearing_instructions_stores_nothing(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_user(session_factory)
    await client.put("/api/v1/preferences", json={"instructions": "Be brief."})

    response = await client.put("/api/v1/preferences", json={"instructions": "   "})

    assert response.status_code == 200, response.text
    assert response.json()["instructions"] is None


async def test_null_is_not_a_partial_update(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_user(session_factory)

    response = await client.put("/api/v1/preferences", json={"instructions": None})

    assert response.status_code == 422


async def test_an_unknown_field_is_refused(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_user(session_factory)

    response = await client.put(
        "/api/v1/preferences", json={"response_style": "casual", "model": "x/y"}
    )

    assert response.status_code == 422


async def test_an_account_never_sees_another_accounts_preferences(
    app, client, session_factory
) -> None:
    await _seed_user(session_factory, OWNER)
    await _seed_user(session_factory, OTHER)
    _current_user(app, OWNER)
    await client.put("/api/v1/preferences", json={"instructions": "Mine only."})

    _current_user(app, OTHER)
    response = await client.get("/api/v1/me")

    assert response.json()["instructions"] is None
    assert response.json()["response_style"] == "default"
