"""Conversation management: states, activity ordering, search, rename, delete."""

import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from ai_chat.auth import get_current_user_id
from ai_chat.auth.models import User
from ai_chat.conversations import service
from ai_chat.conversations.models import Conversation, Message
from ai_chat.llm import ChatChunk, get_chat_provider
from ai_chat.usage.models import TokenUsage

OWNER = "user-1"
OTHER = "user-2"


class _FakeProvider:
    def __init__(self, chunks: list[ChatChunk]) -> None:
        self._chunks = chunks

    async def stream_chat(self, _messages, *, model=None):
        for chunk in self._chunks:
            yield chunk


def _use_provider(app, chunks: list[ChatChunk]) -> None:
    app.dependency_overrides[get_chat_provider] = lambda: _FakeProvider(chunks)


def _current_user(app, user_id: str = OWNER) -> None:
    async def override() -> str:
        return user_id

    app.dependency_overrides[get_current_user_id] = override


async def _seed_users(session_factory, *identifiers: str) -> None:
    async with session_factory() as session:
        for identifier in identifiers or (OWNER,):
            session.add(User(id=identifier, email=f"{identifier}@example.com"))
        await session.commit()


async def _seed_conversation(
    session_factory,
    *,
    user_id: str = OWNER,
    title: str = "New conversation",
    is_pinned: bool = False,
    is_favourite: bool = False,
    is_archived: bool = False,
    activity_at: datetime | None = None,
    messages: Sequence[tuple[str, str]] = (),
) -> uuid.UUID:
    async with session_factory() as session:
        conversation = Conversation(
            user_id=user_id,
            title=title,
            is_pinned=is_pinned,
            is_favourite=is_favourite,
            is_archived=is_archived,
            last_activity_at=activity_at or datetime.now(UTC),
        )
        session.add(conversation)
        await session.flush()
        for role, content in messages:
            session.add(Message(conversation_id=conversation.id, role=role, content=content))
        await session.commit()
        return conversation.id


async def _titles(client, **params) -> list[str]:
    response = await client.get("/api/v1/conversations", params=params)
    assert response.status_code == 200, response.text
    return [item["title"] for item in response.json()["items"]]


async def test_patch_renames_and_sets_the_states(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_users(session_factory)
    conversation_id = await _seed_conversation(session_factory, title="Old name")

    response = await client.patch(
        f"/api/v1/conversations/{conversation_id}", json={"title": "  New name  "}
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == "New name"
    assert body["is_pinned"] is False
    assert body["is_favourite"] is False
    assert body["is_archived"] is False
    assert body["last_activity_at"] is not None

    response = await client.patch(
        f"/api/v1/conversations/{conversation_id}",
        json={"is_pinned": True, "is_favourite": True},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    # The fields that were not sent keep their values.
    assert body["title"] == "New name"
    assert body["is_pinned"] is True
    assert body["is_favourite"] is True
    assert body["is_archived"] is False

    response = await client.patch(
        f"/api/v1/conversations/{conversation_id}",
        json={"is_archived": True, "is_pinned": False},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["is_archived"] is True
    assert body["is_pinned"] is False
    assert body["is_favourite"] is True


async def test_patch_rejects_a_blank_title(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_users(session_factory)
    conversation_id = await _seed_conversation(session_factory)

    response = await client.patch(f"/api/v1/conversations/{conversation_id}", json={"title": "   "})

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


async def test_patch_rejects_a_title_over_the_limit(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_users(session_factory)
    conversation_id = await _seed_conversation(session_factory)

    too_long = await client.patch(
        f"/api/v1/conversations/{conversation_id}", json={"title": "x" * 256}
    )
    at_the_limit = await client.patch(
        f"/api/v1/conversations/{conversation_id}", json={"title": "y" * 255}
    )

    assert too_long.status_code == 422
    assert at_the_limit.status_code == 200
    assert at_the_limit.json()["title"] == "y" * 255


async def test_patch_rejects_unknown_and_null_fields(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_users(session_factory)
    conversation_id = await _seed_conversation(session_factory)

    unknown = await client.patch(
        f"/api/v1/conversations/{conversation_id}", json={"is_favourite": True, "colour": "red"}
    )
    nulled = await client.patch(f"/api/v1/conversations/{conversation_id}", json={"title": None})

    assert unknown.status_code == 422
    assert nulled.status_code == 422


async def test_patch_hides_another_users_conversation(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_users(session_factory, OWNER, OTHER)
    theirs = await _seed_conversation(session_factory, user_id=OTHER, title="Theirs")

    response = await client.patch(f"/api/v1/conversations/{theirs}", json={"title": "Mine now"})

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


async def test_list_is_pinned_first_then_most_recently_active(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_users(session_factory)
    now = datetime.now(UTC)
    await _seed_conversation(session_factory, title="older", activity_at=now - timedelta(hours=2))
    await _seed_conversation(
        session_factory, title="pinned", activity_at=now - timedelta(hours=1), is_pinned=True
    )
    await _seed_conversation(session_factory, title="oldest", activity_at=now - timedelta(hours=3))

    assert await _titles(client) == ["pinned", "older", "oldest"]


async def test_a_new_message_moves_a_conversation_up(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_users(session_factory)
    now = datetime.now(UTC)
    older = await _seed_conversation(
        session_factory, title="older", activity_at=now - timedelta(hours=2)
    )
    await _seed_conversation(session_factory, title="newer", activity_at=now)
    _use_provider(app, [ChatChunk(content="ok")])

    assert await _titles(client) == ["newer", "older"]

    await client.post(f"/api/v1/conversations/{older}/messages", json={"content": "say something"})

    assert await _titles(client) == ["older", "newer"]


async def test_archiving_hides_a_conversation_unless_asked(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_users(session_factory)
    now = datetime.now(UTC)
    await _seed_conversation(session_factory, title="visible", activity_at=now)
    await _seed_conversation(
        session_factory,
        title="archived",
        activity_at=now - timedelta(minutes=1),
        is_archived=True,
    )

    assert await _titles(client) == ["visible"]
    assert await _titles(client, include_archived=True) == ["visible", "archived"]


async def test_search_matches_the_title_and_the_transcript(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_users(session_factory)
    now = datetime.now(UTC)
    await _seed_conversation(session_factory, title="Vector search notes", activity_at=now)
    await _seed_conversation(
        session_factory,
        title="Recipes",
        activity_at=now - timedelta(minutes=1),
        messages=[("user", "how do vector indexes work"), ("assistant", "with cosine")],
    )
    await _seed_conversation(
        session_factory, title="Unrelated", activity_at=now - timedelta(minutes=2)
    )

    assert await _titles(client, q="vector") == ["Vector search notes", "Recipes"]
    # Substring matching is case-insensitive.
    assert await _titles(client, q="VECTOR") == ["Vector search notes", "Recipes"]


async def test_search_is_scoped_to_the_owner(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_users(session_factory, OWNER, OTHER)
    await _seed_conversation(session_factory, title="mine vector")
    await _seed_conversation(session_factory, user_id=OTHER, title="theirs vector")

    assert await _titles(client, q="vector") == ["mine vector"]


async def test_search_leaves_archived_rows_out_unless_asked(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_users(session_factory)
    await _seed_conversation(session_factory, title="archived vector", is_archived=True)

    assert await _titles(client, q="vector") == []
    assert await _titles(client, q="vector", include_archived=True) == ["archived vector"]


async def test_search_treats_wildcards_as_literals(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_users(session_factory)
    now = datetime.now(UTC)
    await _seed_conversation(session_factory, title="100% pure", activity_at=now)
    await _seed_conversation(
        session_factory, title="100X pure", activity_at=now - timedelta(minutes=1)
    )
    await _seed_conversation(
        session_factory, title="a_b plan", activity_at=now - timedelta(minutes=2)
    )
    await _seed_conversation(
        session_factory, title="axb plan", activity_at=now - timedelta(minutes=3)
    )

    assert await _titles(client, q="100%") == ["100% pure"]
    assert await _titles(client, q="a_b") == ["a_b plan"]
    # The escape character itself is a literal too.
    assert await _titles(client, q="\\%") == []


async def test_the_search_term_never_reaches_the_logs(app, client, session_factory, caplog) -> None:
    _current_user(app)
    await _seed_users(session_factory)
    term = "zq9-secret-nonce"
    await _seed_conversation(session_factory, title=f"{term} in the title")

    with caplog.at_level(logging.DEBUG):
        titles = await _titles(client, q=term)

    # The term demonstrably reached the query — it found the row — and the
    # application never logged it (the plan's "the term is never logged").
    assert titles == [f"{term} in the title"]
    assert caplog.records
    # Only the application's own logging is the claim: the SQLite driver echoes
    # every bound parameter at DEBUG and the HTTP client prints the request line,
    # neither of which the application controls.
    logged = " ".join(
        record.getMessage() for record in caplog.records if record.name.startswith("ai_chat")
    )
    assert term not in logged


async def test_delete_removes_the_conversation_and_its_messages(
    app, client, session_factory
) -> None:
    _current_user(app)
    await _seed_users(session_factory)
    conversation_id = await _seed_conversation(
        session_factory,
        title="Doomed",
        messages=[("user", "hello"), ("assistant", "hi")],
    )

    response = await client.delete(f"/api/v1/conversations/{conversation_id}")

    assert response.status_code == 204
    assert response.content == b""
    messages = await client.get(f"/api/v1/conversations/{conversation_id}/messages")
    assert messages.status_code == 404
    assert (await client.delete(f"/api/v1/conversations/{conversation_id}")).status_code == 404

    async with session_factory() as session:
        assert await session.get(Conversation, conversation_id) is None
        remaining = await session.execute(
            select(func.count())
            .select_from(Message)
            .where(Message.conversation_id == conversation_id)
        )
        assert remaining.scalar_one() == 0


async def test_delete_keeps_the_token_ledger(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_users(session_factory)
    conversation_id = await _seed_conversation(session_factory)
    async with session_factory() as session:
        session.add(
            TokenUsage(
                user_id=OWNER,
                conversation_id=conversation_id,
                prompt_tokens=3,
                completion_tokens=7,
                total_tokens=10,
            )
        )
        await session.commit()

    assert (await client.delete(f"/api/v1/conversations/{conversation_id}")).status_code == 204

    async with session_factory() as session:
        rows = (
            await session.execute(select(TokenUsage).where(TokenUsage.user_id == OWNER))
        ).scalars()
        assert [row.total_tokens for row in rows] == [10]


async def test_delete_is_allowed_while_a_stream_holds_the_conversation(
    app, client, session_factory
) -> None:
    """A delete racing a stream wins, and the stream's cleanup still succeeds."""
    _current_user(app)
    await _seed_users(session_factory)
    conversation_id = await _seed_conversation(session_factory)
    async with session_factory() as session:
        conversation = await session.get(Conversation, conversation_id)
        assert conversation is not None
        await service.begin_generation(session, conversation)
        await session.commit()

    response = await client.delete(f"/api/v1/conversations/{conversation_id}")

    assert response.status_code == 204
    # The stream's cleanup runs after the row is gone and must still succeed
    # (ADR-0052): clearing a claim on a row that no longer exists, and stamping
    # activity on it, are both no-ops.
    async with session_factory() as session:
        await service.end_generation(session, conversation_id)
        await service.touch_activity(session, conversation_id)
        assert await session.get(Conversation, conversation_id) is None


async def test_cursor_pagination_walks_the_list_once(session_factory) -> None:
    await _seed_users(session_factory)
    base = datetime.now(UTC) - timedelta(hours=6)
    for index in range(5):
        await _seed_conversation(
            session_factory, title=f"c{index}", activity_at=base + timedelta(minutes=index)
        )
    await _seed_conversation(
        session_factory,
        title="pinned",
        is_pinned=True,
        activity_at=base - timedelta(hours=1),
    )

    async with session_factory() as session:
        first = await service.search_conversations(session, OWNER, limit=2)
        second = await service.search_conversations(
            session, OWNER, limit=2, cursor=first.next_cursor
        )
        third = await service.search_conversations(
            session, OWNER, limit=2, cursor=second.next_cursor
        )

    collected = [item.title for page in (first, second, third) for item in page.items]
    assert collected == ["pinned", "c4", "c3", "c2", "c1", "c0"]
    assert third.next_cursor is None


async def test_cursor_pagination_is_stable_when_the_list_re_sorts(session_factory) -> None:
    await _seed_users(session_factory)
    base = datetime.now(UTC) - timedelta(hours=4)
    for index, title in enumerate(["a", "b", "c", "d"]):
        await _seed_conversation(
            session_factory, title=title, activity_at=base + timedelta(hours=3 - index)
        )

    async with session_factory() as session:
        first = await service.search_conversations(session, OWNER, limit=2)
        assert [item.title for item in first.items] == ["a", "b"]
        # The row at the page boundary is answered again while the client holds
        # the cursor, so it jumps to the front of the list.
        boundary = first.items[-1]
        await service.touch_activity(session, boundary.id, now=datetime.now(UTC))
        await session.commit()
        second = await service.search_conversations(
            session, OWNER, limit=2, cursor=first.next_cursor
        )

    assert [item.title for item in second.items] == ["c", "d"]
    assert not {item.id for item in second.items} & {item.id for item in first.items}


async def test_the_route_pages_a_hundred_at_a_time(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_users(session_factory)
    base = datetime.now(UTC) - timedelta(days=1)
    async with session_factory() as session:
        session.add_all(
            [
                Conversation(
                    user_id=OWNER,
                    title=f"row-{index:03d}",
                    last_activity_at=base + timedelta(seconds=index),
                )
                for index in range(101)
            ]
        )
        await session.commit()

    first = (await client.get("/api/v1/conversations")).json()
    assert len(first["items"]) == 100
    assert first["items"][0]["title"] == "row-100"
    assert first["next_cursor"] is not None

    second = (
        await client.get("/api/v1/conversations", params={"cursor": first["next_cursor"]})
    ).json()
    assert [item["title"] for item in second["items"]] == ["row-000"]
    assert second["next_cursor"] is None


async def test_a_malformed_cursor_is_rejected(app, client, session_factory) -> None:
    _current_user(app)
    await _seed_users(session_factory)

    response = await client.get("/api/v1/conversations", params={"cursor": "not-a-cursor"})

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_CURSOR"
