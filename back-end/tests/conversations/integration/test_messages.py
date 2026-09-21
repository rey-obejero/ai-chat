import json
import uuid

from ai_chat.auth import get_current_user_id
from ai_chat.auth.models import User
from ai_chat.conversations.models import Conversation, Message
from ai_chat.llm import ChatChunk, get_chat_provider


class _FakeProvider:
    def __init__(self, chunks: list[ChatChunk]) -> None:
        self._chunks = chunks

    async def stream_chat(self, _messages, *, model=None):
        for chunk in self._chunks:
            yield chunk


def _use_provider(app, chunks: list[ChatChunk]) -> None:
    app.dependency_overrides[get_chat_provider] = lambda: _FakeProvider(chunks)


def _current_user(app, user_id: str = "user-1") -> None:
    async def override() -> str:
        return user_id

    app.dependency_overrides[get_current_user_id] = override


def _parts(response) -> list[object]:
    lines = [line for line in response.text.splitlines() if line.startswith("data: ")]
    payloads = [line.removeprefix("data: ") for line in lines]
    return [payload if payload == "[DONE]" else json.loads(payload) for payload in payloads]


async def _seed_conversation(session_factory, user_id: str = "user-1") -> uuid.UUID:
    async with session_factory() as session:
        session.add(User(id=user_id, email=f"{user_id}@example.com"))
        conversation = Conversation(user_id=user_id, title="New conversation")
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        return conversation.id


async def test_create_conversation(app, client) -> None:
    _current_user(app)

    response = await client.post("/api/v1/conversations")

    assert response.status_code == 201
    assert response.json()["title"] == "New conversation"


async def test_send_message_streams_the_reply_and_persists_it(app, client, session_factory) -> None:
    conversation_id = await _seed_conversation(session_factory)
    _current_user(app)
    _use_provider(app, [ChatChunk(content="Hi "), ChatChunk(content="there")])

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "Hello"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-vercel-ai-ui-message-stream"] == "v1"

    parts = _parts(response)
    assert parts[-1] == "[DONE]"
    types = [part["type"] for part in parts[:-1]]
    assert types == ["start", "text-start", "text-delta", "text-delta", "text-end", "finish"]
    deltas = [part["delta"] for part in parts if isinstance(part, dict) and "delta" in part]
    assert deltas == ["Hi ", "there"]

    history = await client.get(f"/api/v1/conversations/{conversation_id}/messages")
    roles_and_content = [(item["role"], item["content"]) for item in history.json()]
    assert roles_and_content == [("user", "Hello"), ("assistant", "Hi there")]


async def test_first_message_names_the_conversation(app, client, session_factory) -> None:
    conversation_id = await _seed_conversation(session_factory)
    _current_user(app)
    _use_provider(app, [ChatChunk(content="ok")])

    await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "Explain vector search\nin one line"},
    )

    conversations = await client.get("/api/v1/conversations")
    assert conversations.json()[0]["title"] == "Explain vector search"


async def test_provider_failure_is_reported_as_an_error_part(app, client, session_factory) -> None:
    conversation_id = await _seed_conversation(session_factory)
    _current_user(app)

    class _Exploding:
        async def stream_chat(self, _messages, *, model=None):
            yield ChatChunk(content="partial")
            raise RuntimeError("provider vanished")

    app.dependency_overrides[get_chat_provider] = lambda: _Exploding()

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "Hello"},
    )

    parts = _parts(response)
    assert parts[-1] == "[DONE]"
    assert any(isinstance(part, dict) and part["type"] == "error" for part in parts)

    history = await client.get(f"/api/v1/conversations/{conversation_id}/messages")
    assert [item["role"] for item in history.json()] == ["user"]


async def test_other_users_conversations_are_not_visible(app, client, session_factory) -> None:
    conversation_id = await _seed_conversation(session_factory, user_id="user-1")
    _current_user(app, user_id="user-2")

    response = await client.get(f"/api/v1/conversations/{conversation_id}/messages")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


async def test_blank_message_is_rejected(app, client, session_factory) -> None:
    conversation_id = await _seed_conversation(session_factory)
    _current_user(app)
    _use_provider(app, [])

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": ""},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


async def test_messages_are_ordered_oldest_first(session_factory) -> None:
    from ai_chat.conversations import service

    conversation_id = await _seed_conversation(session_factory)
    async with session_factory() as session:
        conversation = await session.get(Conversation, conversation_id)
        await service.add_message(session, conversation, role="user", content="first")
        await service.add_message(session, conversation, role="assistant", content="second")
        rows = await service.list_messages(session, conversation.id)

    assert [row.content for row in rows] == ["first", "second"]
    assert all(isinstance(row, Message) for row in rows)
