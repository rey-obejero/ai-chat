"""The account's display name and the first-run prompt (FR-7, ADR-0045).

Creation names the account, `PATCH /me` renames it or records the skipped
prompt, and a name that will not do is refused with a reason — never masked or
silently renamed.
"""

from ai_chat.auth import get_current_user_id
from ai_chat.auth.models import User

OWNER = "user-1"
OTHER = "user-2"
DERIVED = "amara.okafor"


def _current_user(app, user_id: str = OWNER) -> None:
    async def override() -> str:
        return user_id

    app.dependency_overrides[get_current_user_id] = override


async def _seed_user(session_factory, user_id: str = OWNER, display_name: str = DERIVED) -> None:
    async with session_factory() as session:
        session.add(User(id=user_id, email=f"{user_id}@example.com", display_name=display_name))
        await session.commit()


def _address(email: str):
    async def fake_email(_user_id: str) -> str:
        return email

    return fake_email


async def test_a_new_account_is_named_from_its_email(app, client, monkeypatch) -> None:
    _current_user(app)
    monkeypatch.setattr("ai_chat.auth.service.get_email", _address("amara.okafor@example.com"))

    response = await client.get("/api/v1/me")

    assert response.status_code == 200
    assert response.json()["display_name"] == DERIVED
    # The prompt is still owed: the derived name is not an answer to it.
    assert response.json()["name_prompt_seen"] is False


async def test_an_address_with_nothing_to_derive_still_names_the_account(
    app, client, monkeypatch
) -> None:
    _current_user(app)
    monkeypatch.setattr("ai_chat.auth.service.get_email", _address("@example.com"))

    response = await client.get("/api/v1/me")

    assert response.json()["display_name"] == "User"


async def test_saving_a_name_answers_the_prompt(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_user(session_factory)

    response = await client.patch("/api/v1/me", json={"display_name": "  Amara Okafor  "})

    assert response.status_code == 200, response.text
    saved = response.json()
    assert saved["display_name"] == "Amara Okafor"
    # Naming yourself is the prompt's answer, so the flag follows the name.
    assert saved["name_prompt_seen"] is True
    assert (await client.get("/api/v1/me")).json() == saved


async def test_a_saved_name_is_stored_composed(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_user(session_factory)

    response = await client.patch("/api/v1/me", json={"display_name": "Jose\u0301"})

    assert response.status_code == 200, response.text
    assert response.json()["display_name"] == "José"


async def test_the_prompt_is_answered_by_naming_even_if_the_flag_says_otherwise(
    app, client, session_factory
) -> None:
    # A contradiction: the request names itself and claims the prompt was not
    # answered. The name wins, because saving the name is the answer.
    _current_user(app)
    await _seed_user(session_factory)

    response = await client.patch(
        "/api/v1/me", json={"display_name": "Amara", "name_prompt_seen": False}
    )

    assert response.status_code == 200, response.text
    assert response.json()["display_name"] == "Amara"
    assert response.json()["name_prompt_seen"] is True


async def test_skipping_records_the_flag_and_keeps_the_derived_name(
    app, client, session_factory
) -> None:
    _current_user(app)
    await _seed_user(session_factory)

    response = await client.patch("/api/v1/me", json={"name_prompt_seen": True})

    assert response.status_code == 200, response.text
    assert response.json()["display_name"] == DERIVED
    assert response.json()["name_prompt_seen"] is True


async def test_an_empty_patch_changes_nothing(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_user(session_factory)
    before = (await client.get("/api/v1/me")).json()

    response = await client.patch("/api/v1/me", json={})

    assert response.status_code == 200, response.text
    assert response.json() == before


async def test_an_empty_name_is_refused(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_user(session_factory)

    response = await client.patch("/api/v1/me", json={"display_name": "   "})

    assert response.status_code == 422
    assert "required" in response.json()["errors"][0]["message"]
    # The refusal leaves the account alone rather than blanking the name.
    assert (await client.get("/api/v1/me")).json()["display_name"] == DERIVED


async def test_the_cap_is_measured_after_trimming(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_user(session_factory)

    over = await client.patch("/api/v1/me", json={"display_name": f"  {'x' * 51}  "})
    at_cap = await client.patch("/api/v1/me", json={"display_name": f"  {'x' * 50}  "})

    assert over.status_code == 422
    assert "at most 50 characters" in over.json()["errors"][0]["message"]
    assert at_cap.status_code == 200, at_cap.text
    assert at_cap.json()["display_name"] == "x" * 50


async def test_a_name_with_a_control_character_is_refused(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_user(session_factory)

    response = await client.patch("/api/v1/me", json={"display_name": "Amara\nOkafor"})

    assert response.status_code == 422
    assert "control characters" in response.json()["errors"][0]["message"]
    assert (await client.get("/api/v1/me")).json()["display_name"] == DERIVED


async def test_a_profane_name_is_refused_with_a_readable_reason(
    app, client, session_factory
) -> None:
    _current_user(app)
    await _seed_user(session_factory)

    response = await client.patch("/api/v1/me", json={"display_name": "Amara Shit Okafor"})

    assert response.status_code == 422
    assert "not allowed" in response.json()["errors"][0]["message"]
    # Nothing is masked or renamed behind the account's back: the old name stands.
    stored = (await client.get("/api/v1/me")).json()
    assert stored["display_name"] == DERIVED
    assert stored["name_prompt_seen"] is False


async def test_null_is_not_a_partial_update(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_user(session_factory)

    response = await client.patch("/api/v1/me", json={"display_name": None})

    assert response.status_code == 422


async def test_an_unknown_field_is_refused(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_user(session_factory)

    response = await client.patch("/api/v1/me", json={"display_name": "Amara", "email": "x@y"})

    assert response.status_code == 422


async def test_an_account_never_reaches_another_accounts_name(app, client, session_factory) -> None:
    await _seed_user(session_factory, OTHER, "Obi")
    _current_user(app, OTHER)

    response = await client.patch("/api/v1/me", json={"display_name": "Obi Wan"})

    assert response.status_code == 200, response.text
    assert response.json()["display_name"] == "Obi Wan"
    assert (await client.get("/api/v1/me")).json()["display_name"] == "Obi Wan"
