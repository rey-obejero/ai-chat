"""Edit and regenerate: truncation, the generation gate, and idempotency."""

import json
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from ai_chat.auth import get_current_user_id
from ai_chat.auth.models import User
from ai_chat.conversations.models import Conversation, Message
from ai_chat.conversations.streaming import stream_reply
from ai_chat.llm import ChatChunk, TokenUsage, get_chat_provider
from ai_chat.usage import service as usage_service


class _FakeProvider:
    def __init__(self, chunks: list[ChatChunk], calls: list[int] | None = None) -> None:
        self._chunks = chunks
        self._calls = calls

    async def stream_chat(self, _messages, *, model=None):
        if self._calls is not None:
            self._calls.append(1)
        for chunk in self._chunks:
            yield chunk


class _RecordingProvider(_FakeProvider):
    """A provider that reports how far it got and whether it was closed."""

    def __init__(self, chunks: list[ChatChunk]) -> None:
        super().__init__(chunks)
        self.pulled = 0
        self.closed = False

    async def stream_chat(self, _messages, *, model=None):
        try:
            for chunk in self._chunks:
                self.pulled += 1
                yield chunk
        finally:
            self.closed = True


class _Disconnects:
    """A stand-in for ``request.is_disconnected`` that trips on a given tick."""

    def __init__(self, *, after: int) -> None:
        self._after = after
        self.calls = 0

    async def __call__(self) -> bool:
        self.calls += 1
        return self.calls > self._after


def _use_provider(app, chunks: list[ChatChunk], calls: list[int] | None = None) -> None:
    app.dependency_overrides[get_chat_provider] = lambda: _FakeProvider(chunks, calls)


def _current_user(app, user_id: str = "user-1") -> None:
    async def override() -> str:
        return user_id

    app.dependency_overrides[get_current_user_id] = override


def _parts(response) -> list[object]:
    lines = [line for line in response.text.splitlines() if line.startswith("data: ")]
    payloads = [line.removeprefix("data: ") for line in lines]
    return [payload if payload == "[DONE]" else json.loads(payload) for payload in payloads]


def _turns(messages: list[dict]) -> list[tuple[str, str]]:
    return [(item["role"], item["content"]) for item in messages]


def _events(parts: list[str]) -> list[object]:
    """Decode the SSE strings a stream generator yields directly."""
    payloads = [part.removeprefix("data: ").strip() for part in parts if part.startswith("data: ")]
    return [payload if payload == "[DONE]" else json.loads(payload) for payload in payloads]


async def _seed(
    session_factory,
    *,
    user_id: str = "user-1",
    messages: Sequence[tuple[str, str] | tuple[str, str, uuid.UUID]] = (),
) -> uuid.UUID:
    """A conversation with explicitly ordered turns, so truncation is deterministic.

    A third tuple element gives that turn a client key, the way a send does.
    """
    async with session_factory() as session:
        if await session.get(User, user_id) is None:
            session.add(User(id=user_id, email=f"{user_id}@example.com"))
        conversation = Conversation(user_id=user_id, title="New conversation")
        session.add(conversation)
        await session.commit()
        base = datetime.now(UTC)
        for index, entry in enumerate(messages):
            role, content = entry[0], entry[1]
            client_id = entry[2] if len(entry) > 2 else None
            session.add(
                Message(
                    conversation_id=conversation.id,
                    role=role,
                    content=content,
                    client_id=client_id,
                    created_at=base + timedelta(seconds=index),
                )
            )
        if messages:
            await session.commit()
        return conversation.id


async def _message_id(session_factory, conversation_id: uuid.UUID, *, role: str) -> uuid.UUID:
    async with session_factory() as session:
        result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id, Message.role == role)
            .order_by(Message.created_at, Message.id)
        )
        return result.scalars().first().id


async def _gate(session_factory, conversation_id: uuid.UUID) -> datetime | None:
    async with session_factory() as session:
        conversation = await session.get(Conversation, conversation_id)
        return conversation.generating_at


async def _history(client, conversation_id: uuid.UUID) -> list[tuple[str, str]]:
    response = await client.get(f"/api/v1/conversations/{conversation_id}/messages")
    return _turns(response.json())


async def test_editing_a_user_message_replaces_it_and_truncates_everything_after(
    app, client, session_factory
) -> None:
    conversation_id = await _seed(
        session_factory,
        messages=[
            ("user", "original"),
            ("assistant", "first reply"),
            ("user", "later"),
            ("assistant", "later reply"),
        ],
    )
    _current_user(app)
    _use_provider(app, [ChatChunk(content="edited "), ChatChunk(content="reply")])
    message_id = await _message_id(session_factory, conversation_id, role="user")

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages/{message_id}/edit",
        json={"content": "edited"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    parts = _parts(response)
    assert parts[-1] == "[DONE]"
    assert [part["type"] for part in parts[:-1]] == [
        "start",
        "text-start",
        "text-delta",
        "text-delta",
        "text-end",
        "finish",
    ]
    assert await _history(client, conversation_id) == [
        ("user", "edited"),
        ("assistant", "edited reply"),
    ]
    assert await _gate(session_factory, conversation_id) is None


async def test_a_live_turn_is_editable_by_its_client_id(app, client, session_factory) -> None:
    """The path id is the client's own, non-server id; the key addresses the turn."""
    key = uuid.uuid4()
    conversation_id = await _seed(
        session_factory,
        messages=[
            ("user", "original", key),
            ("assistant", "first reply"),
            ("user", "later"),
            ("assistant", "later reply"),
        ],
    )
    _current_user(app)
    calls: list[int] = []
    _use_provider(app, [ChatChunk(content="edited reply")], calls=calls)
    url = f"/api/v1/conversations/{conversation_id}/messages/ui-message-1/edit"

    response = await client.post(url, json={"content": "edited", "client_id": str(key)})
    retry = await client.post(url, json={"content": "edited", "client_id": str(key)})

    assert response.status_code == 200
    assert retry.status_code == 200
    assert await _history(client, conversation_id) == [
        ("user", "edited"),
        ("assistant", "edited reply"),
    ]
    assert len(calls) == 1, "the retry replays the reply instead of rewriting again"


async def test_a_foreign_path_id_still_resolves_by_the_key(app, client, session_factory) -> None:
    key = uuid.uuid4()
    conversation_id = await _seed(session_factory, messages=[("user", "original", key)])
    other_id = await _seed(session_factory, messages=[("user", "elsewhere")])
    _current_user(app)
    _use_provider(app, [ChatChunk(content="edited reply")])
    foreign = await _message_id(session_factory, other_id, role="user")

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages/{foreign}/edit",
        json={"content": "edited", "client_id": str(key)},
    )

    assert response.status_code == 200
    assert await _history(client, conversation_id) == [
        ("user", "edited"),
        ("assistant", "edited reply"),
    ]


async def test_an_unresolvable_edit_is_a_404(app, client, session_factory) -> None:
    conversation_id = await _seed(session_factory, messages=[("user", "hello")])
    _current_user(app)
    _use_provider(app, [ChatChunk(content="never sent")])

    local_only = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages/ui-message-1/edit",
        json={"content": "nope"},
    )
    unknown_key = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages/ui-message-1/edit",
        json={"content": "nope", "client_id": str(uuid.uuid4())},
    )

    for response in (local_only, unknown_key):
        assert response.status_code == 404
        assert response.json()["code"] == "NOT_FOUND"
    assert await _history(client, conversation_id) == [("user", "hello")]


async def test_a_server_uuid_outranks_the_key(app, client, session_factory) -> None:
    """A path naming an assistant turn still 409s, whatever key comes with it."""
    key = uuid.uuid4()
    conversation_id = await _seed(
        session_factory, messages=[("user", "hello", key), ("assistant", "hi there")]
    )
    _current_user(app)
    _use_provider(app, [ChatChunk(content="never sent")])
    assistant_id = await _message_id(session_factory, conversation_id, role="assistant")

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages/{assistant_id}/edit",
        json={"content": "nope", "client_id": str(key)},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_OPERATION"


async def test_the_message_list_exposes_each_turns_key(app, client, session_factory) -> None:
    key = uuid.uuid4()
    conversation_id = await _seed(
        session_factory, messages=[("user", "hello", key), ("assistant", "hi there")]
    )
    _current_user(app)

    response = await client.get(f"/api/v1/conversations/{conversation_id}/messages")

    turns = response.json()
    assert turns[0]["client_id"] == str(key)
    assert turns[1]["client_id"] is None


async def test_regenerating_an_assistant_message_drops_it_and_everything_after(
    app, client, session_factory
) -> None:
    conversation_id = await _seed(
        session_factory,
        messages=[
            ("user", "hello"),
            ("assistant", "first"),
            ("user", "again"),
            ("assistant", "second"),
        ],
    )
    _current_user(app)
    _use_provider(app, [ChatChunk(content="regenerated")])
    message_id = await _message_id(session_factory, conversation_id, role="assistant")

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages/{message_id}/regenerate"
    )

    assert response.status_code == 200
    assert await _history(client, conversation_id) == [
        ("user", "hello"),
        ("assistant", "regenerated"),
    ]


async def test_regenerating_the_only_message_leaves_an_empty_history(
    app, client, session_factory
) -> None:
    conversation_id = await _seed(session_factory, messages=[("assistant", "orphan")])
    _current_user(app)
    _use_provider(app, [ChatChunk(content="fresh")])
    message_id = await _message_id(session_factory, conversation_id, role="assistant")

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages/{message_id}/regenerate"
    )

    assert response.status_code == 200
    assert await _history(client, conversation_id) == [("assistant", "fresh")]


async def test_editing_an_assistant_message_is_a_409(app, client, session_factory) -> None:
    conversation_id = await _seed(
        session_factory, messages=[("user", "hello"), ("assistant", "hi there")]
    )
    _current_user(app)
    _use_provider(app, [ChatChunk(content="never sent")])
    message_id = await _message_id(session_factory, conversation_id, role="assistant")

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages/{message_id}/edit",
        json={"content": "nope"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_OPERATION"
    assert await _history(client, conversation_id) == [
        ("user", "hello"),
        ("assistant", "hi there"),
    ]


async def test_regenerating_a_user_message_is_a_409(app, client, session_factory) -> None:
    conversation_id = await _seed(
        session_factory, messages=[("user", "hello"), ("assistant", "hi there")]
    )
    _current_user(app)
    _use_provider(app, [ChatChunk(content="never sent")])
    message_id = await _message_id(session_factory, conversation_id, role="user")

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages/{message_id}/regenerate"
    )

    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_OPERATION"
    assert await _history(client, conversation_id) == [
        ("user", "hello"),
        ("assistant", "hi there"),
    ]


async def test_a_message_of_another_conversation_is_a_404(app, client, session_factory) -> None:
    conversation_id = await _seed(session_factory, messages=[("user", "hello")])
    other_id = await _seed(session_factory, messages=[("user", "elsewhere")])
    _current_user(app)
    _use_provider(app, [ChatChunk(content="never sent")])
    message_id = await _message_id(session_factory, other_id, role="user")

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages/{message_id}/edit",
        json={"content": "nope"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


async def test_another_users_conversation_is_a_404(app, client, session_factory) -> None:
    conversation_id = await _seed(session_factory, user_id="user-1", messages=[("user", "hello")])
    _current_user(app, user_id="user-2")
    _use_provider(app, [ChatChunk(content="never sent")])
    message_id = await _message_id(session_factory, conversation_id, role="user")

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages/{message_id}/edit",
        json={"content": "nope"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


async def test_a_repeated_client_id_does_not_duplicate_the_send(
    app, client, session_factory
) -> None:
    conversation_id = await _seed(session_factory)
    _current_user(app)
    calls: list[int] = []
    _use_provider(app, [ChatChunk(content="Hi there")], calls=calls)
    key = str(uuid.uuid4())
    url = f"/api/v1/conversations/{conversation_id}/messages"

    first = await client.post(url, json={"content": "Hello", "client_id": key})
    second = await client.post(url, json={"content": "Hello", "client_id": key})

    assert first.status_code == 200
    assert second.status_code == 200
    assert await _history(client, conversation_id) == [
        ("user", "Hello"),
        ("assistant", "Hi there"),
    ]
    assert len(calls) == 1, "a retry must not spend tokens again"
    deltas = [
        part["delta"] for part in _parts(second) if isinstance(part, dict) and "delta" in part
    ]
    assert deltas == ["Hi there"]


async def test_a_repeated_edit_client_id_does_not_rewrite_again(
    app, client, session_factory
) -> None:
    conversation_id = await _seed(
        session_factory, messages=[("user", "original"), ("assistant", "first reply")]
    )
    _current_user(app)
    calls: list[int] = []
    _use_provider(app, [ChatChunk(content="edited reply")], calls=calls)
    message_id = await _message_id(session_factory, conversation_id, role="user")
    key = str(uuid.uuid4())
    url = f"/api/v1/conversations/{conversation_id}/messages/{message_id}/edit"

    first = await client.post(url, json={"content": "edited", "client_id": key})
    second = await client.post(url, json={"content": "second guess", "client_id": key})

    assert first.status_code == 200
    assert second.status_code == 200
    assert await _history(client, conversation_id) == [
        ("user", "edited"),
        ("assistant", "edited reply"),
    ]
    assert len(calls) == 1


async def test_a_repeated_regenerate_client_id_does_not_rewrite_again(
    app, client, session_factory
) -> None:
    conversation_id = await _seed(
        session_factory, messages=[("user", "hello"), ("assistant", "first")]
    )
    _current_user(app)
    calls: list[int] = []
    _use_provider(app, [ChatChunk(content="regenerated")], calls=calls)
    message_id = await _message_id(session_factory, conversation_id, role="assistant")
    key = str(uuid.uuid4())
    url = f"/api/v1/conversations/{conversation_id}/messages/{message_id}/regenerate"

    first = await client.post(url, json={"client_id": key})
    # The retry names a message the first attempt deleted; the key still wins.
    second = await client.post(url, json={"client_id": key})

    assert first.status_code == 200
    assert second.status_code == 200
    assert await _history(client, conversation_id) == [
        ("user", "hello"),
        ("assistant", "regenerated"),
    ]
    assert len(calls) == 1


async def test_a_second_writer_loses_while_a_stream_holds_the_gate(
    app, client, session_factory
) -> None:
    conversation_id = await _seed(
        session_factory, messages=[("user", "hello"), ("assistant", "hi there")]
    )
    _current_user(app)
    _use_provider(app, [ChatChunk(content="never sent")])
    user_message_id = await _message_id(session_factory, conversation_id, role="user")
    assistant_message_id = await _message_id(session_factory, conversation_id, role="assistant")
    async with session_factory() as session:
        conversation = await session.get(Conversation, conversation_id)
        conversation.generating_at = datetime.now(UTC)
        await session.commit()

    send = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages", json={"content": "again"}
    )
    edit = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages/{user_message_id}/edit",
        json={"content": "changed"},
    )
    regenerate = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages/{assistant_message_id}/regenerate"
    )

    for response in (send, edit, regenerate):
        assert response.status_code == 409
        assert response.json()["code"] == "CONVERSATION_BUSY"
    assert await _history(client, conversation_id) == [
        ("user", "hello"),
        ("assistant", "hi there"),
    ]


async def test_a_stale_gate_does_not_wedge_the_conversation(app, client, session_factory) -> None:
    conversation_id = await _seed(session_factory)
    _current_user(app)
    _use_provider(app, [ChatChunk(content="recovered")])
    async with session_factory() as session:
        conversation = await session.get(Conversation, conversation_id)
        conversation.generating_at = datetime.now(UTC) - timedelta(seconds=3600)
        await session.commit()

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages", json={"content": "hello"}
    )

    assert response.status_code == 200
    assert await _history(client, conversation_id) == [
        ("user", "hello"),
        ("assistant", "recovered"),
    ]
    assert await _gate(session_factory, conversation_id) is None


async def test_a_spent_quota_blocks_an_edit_without_touching_the_transcript(
    quota_app, quota_client, session_factory
) -> None:
    conversation_id = await _seed(
        session_factory, messages=[("user", "hello"), ("assistant", "hi there")]
    )
    _current_user(quota_app)
    _use_provider(quota_app, [ChatChunk(content="never sent")])
    message_id = await _message_id(session_factory, conversation_id, role="user")
    async with session_factory() as session:
        await usage_service.record(
            session, user_id="user-1", conversation_id=None, usage=TokenUsage(total_tokens=1000)
        )

    response = await quota_client.post(
        f"/api/v1/conversations/{conversation_id}/messages/{message_id}/edit",
        json={"content": "changed"},
    )

    assert response.status_code == 429
    assert response.json()["code"] == "QUOTA_EXCEEDED"
    assert await _history(quota_client, conversation_id) == [
        ("user", "hello"),
        ("assistant", "hi there"),
    ]
    usage = await quota_client.get("/api/v1/usage")
    assert usage.json()["used"] == 1000


async def test_a_disconnect_keeps_the_partial_and_clears_the_gate(session_factory) -> None:
    conversation_id = await _seed(session_factory, messages=[("user", "hello")])
    async with session_factory() as session:
        conversation = await session.get(Conversation, conversation_id)
        conversation.generating_at = datetime.now(UTC)
        await session.commit()
    provider = _RecordingProvider(
        [
            ChatChunk(content="a"),
            ChatChunk(content="b"),
            ChatChunk(content="c"),
            ChatChunk(content="d"),
        ]
    )
    disconnected = _Disconnects(after=2)

    events = stream_reply(
        provider=provider,
        conversation_id=conversation_id,
        user_id="user-1",
        history=[],
        session_factory=session_factory,
        is_disconnected=disconnected,
    )
    parts = [part async for part in events]
    events_decoded = _events(parts)

    assert disconnected.calls == 3
    assert provider.closed is True
    assert provider.pulled == 3
    assert not any(isinstance(part, dict) and part["type"] == "error" for part in events_decoded)
    assert not any(isinstance(part, dict) and part["type"] == "finish" for part in events_decoded)
    deltas = [
        part["delta"] for part in events_decoded if isinstance(part, dict) and "delta" in part
    ]
    assert deltas == ["a", "b"]

    assert await _history_via_db(session_factory, conversation_id) == [
        ("user", "hello"),
        ("assistant", "ab"),
    ]
    assert await _gate(session_factory, conversation_id) is None


async def test_closing_the_stream_keeps_the_partial_and_clears_the_gate(session_factory) -> None:
    conversation_id = await _seed(session_factory, messages=[("user", "hello")])
    async with session_factory() as session:
        conversation = await session.get(Conversation, conversation_id)
        conversation.generating_at = datetime.now(UTC)
        await session.commit()
    provider = _RecordingProvider([ChatChunk(content="a"), ChatChunk(content="b")])

    events = stream_reply(
        provider=provider,
        conversation_id=conversation_id,
        user_id="user-1",
        history=[],
        session_factory=session_factory,
    )
    await anext(events)  # start
    await anext(events)  # text-start
    await anext(events)  # first delta
    await events.aclose()

    assert provider.closed is True
    assert await _history_via_db(session_factory, conversation_id) == [
        ("user", "hello"),
        ("assistant", "a"),
    ]
    assert await _gate(session_factory, conversation_id) is None


async def _history_via_db(session_factory, conversation_id: uuid.UUID) -> list[tuple[str, str]]:
    async with session_factory() as session:
        result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at, Message.id)
        )
        return [(row.role, row.content) for row in result.scalars().all()]
