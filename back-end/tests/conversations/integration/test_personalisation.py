"""Personalisation: the account's prompt, and the conversation's model (FR-23–25)."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from ai_chat.auth import get_current_user_id
from ai_chat.auth.models import User
from ai_chat.conversations.models import Conversation, Message
from ai_chat.conversations.streaming import _persist_assistant_message
from ai_chat.llm import STYLE_FRAGMENTS, ChatChunk, ResponseStyle, get_chat_provider

OWNER = "user-1"
OTHER = "user-2"
DEFAULT_MODEL = "openai/gpt-4o-mini"
SECOND_MODEL = "anthropic/claude-haiku"
# A model this deployment does not serve: what a stored choice becomes when an
# operator removes it from `llm_models` (M5).
RETIRED_MODEL = "someone/retired-model"
INSTRUCTIONS = "Answer in British English."


class _CapturingProvider:
    """A provider that records the prompt and the model it was called with."""

    def __init__(self, chunks: list[ChatChunk] | None = None) -> None:
        self._chunks = [ChatChunk(content="ok")] if chunks is None else chunks
        self.sent: list[list[tuple[str, str]]] = []
        self.models: list[str | None] = []

    async def stream_chat(self, messages, *, model=None):
        self.sent.append([(message.role.value, message.content) for message in messages])
        self.models.append(model)
        for chunk in self._chunks:
            yield chunk


def _use_provider(app, provider: _CapturingProvider) -> None:
    app.dependency_overrides[get_chat_provider] = lambda: provider


def _current_user(app, user_id: str = OWNER) -> None:
    async def override() -> str:
        return user_id

    app.dependency_overrides[get_current_user_id] = override


async def _seed(
    session_factory,
    *,
    user_id: str = OWNER,
    model: str | None = None,
    instructions: str | None = None,
    response_style: str = "default",
    messages: Sequence[tuple[str, str]] = (),
) -> uuid.UUID:
    """A conversation, its owner, and an explicitly ordered transcript."""
    async with session_factory() as session:
        if await session.get(User, user_id) is None:
            session.add(
                User(
                    id=user_id,
                    email=f"{user_id}@example.com",
                    instructions=instructions,
                    response_style=response_style,
                )
            )
        conversation = Conversation(user_id=user_id, title="New conversation", model=model)
        session.add(conversation)
        await session.flush()
        base = datetime.now(UTC)
        for index, (role, content) in enumerate(messages):
            session.add(
                Message(
                    conversation_id=conversation.id,
                    role=role,
                    content=content,
                    created_at=base + timedelta(seconds=index),
                )
            )
        await session.commit()
        return conversation.id


async def _send(client, conversation_id: uuid.UUID, content: str = "Hello") -> None:
    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages", json={"content": content}
    )
    assert response.status_code == 200, response.text


async def _transcript(client, conversation_id: uuid.UUID) -> list[tuple[str, str]]:
    response = await client.get(f"/api/v1/conversations/{conversation_id}/messages")
    assert response.status_code == 200, response.text
    return [(item["role"], item["content"]) for item in response.json()]


async def _stored_model(session_factory, conversation_id: uuid.UUID) -> str | None:
    async with session_factory() as session:
        conversation = await session.get(Conversation, conversation_id)
        return conversation.model


async def test_the_account_prompt_leads_the_transcript(app, client, session_factory) -> None:
    conversation_id = await _seed(
        session_factory, instructions=INSTRUCTIONS, response_style="concise"
    )
    _current_user(app)
    provider = _CapturingProvider()
    _use_provider(app, provider)

    await _send(client, conversation_id)

    prompt = f"{INSTRUCTIONS}\n\n{STYLE_FRAGMENTS[ResponseStyle.CONCISE]}"
    assert provider.sent == [[("system", prompt), ("user", "Hello")]]


async def test_an_account_without_preferences_sends_no_system_prompt(
    app, client, session_factory
) -> None:
    conversation_id = await _seed(session_factory)
    _current_user(app)
    provider = _CapturingProvider()
    _use_provider(app, provider)

    await _send(client, conversation_id)

    assert provider.sent == [[("user", "Hello")]]
    assert provider.models == [DEFAULT_MODEL]


async def test_the_chosen_model_is_used_on_every_turn(
    two_model_app, two_model_client, session_factory
) -> None:
    conversation_id = await _seed(session_factory, model=SECOND_MODEL)
    _current_user(two_model_app)
    provider = _CapturingProvider()
    _use_provider(two_model_app, provider)

    await _send(two_model_client, conversation_id, "First")
    await _send(two_model_client, conversation_id, "Second")

    assert provider.models == [SECOND_MODEL, SECOND_MODEL]
    assert await _stored_model(session_factory, conversation_id) == SECOND_MODEL


async def test_a_conversation_without_a_model_uses_the_default(
    app, client, session_factory
) -> None:
    conversation_id = await _seed(session_factory)
    _current_user(app)
    provider = _CapturingProvider()
    _use_provider(app, provider)

    await _send(client, conversation_id)

    assert provider.models == [DEFAULT_MODEL]
    assert await _stored_model(session_factory, conversation_id) is None


async def test_a_switch_persists_a_caption_and_applies_to_the_next_reply(
    two_model_app, two_model_client, session_factory
) -> None:
    conversation_id = await _seed(session_factory, messages=[("user", "Hello")])
    _current_user(two_model_app)
    provider = _CapturingProvider()
    _use_provider(two_model_app, provider)

    response = await two_model_client.patch(
        f"/api/v1/conversations/{conversation_id}", json={"model": SECOND_MODEL}
    )

    assert response.status_code == 200, response.text
    assert response.json()["model"] == SECOND_MODEL
    caption = ("system", f"Model set to {SECOND_MODEL}")
    assert await _transcript(two_model_client, conversation_id) == [("user", "Hello"), caption]

    await _send(two_model_client, conversation_id, "Now in the other model")

    # The transcript is what the provider sees, caption included, and the reply
    # goes to the model the caption named.
    assert provider.sent == [[("user", "Hello"), caption, ("user", "Now in the other model")]]
    assert provider.models == [SECOND_MODEL]


async def test_a_caption_written_mid_stream_sorts_after_the_reply(
    two_model_app, two_model_client, session_factory
) -> None:
    """The switch's caption belongs after the answer it interrupted (FR-23).

    A reply is stamped with the moment its stream began, so a caption written
    while it was still streaming cannot land in front of it and claim an answer
    the previous model made.
    """
    conversation_id = await _seed(session_factory, messages=[("user", "Hello")])
    _current_user(two_model_app)
    async with session_factory() as session:
        # The turn happened a while ago; the reply below began a second ago.
        await session.execute(
            update(Message).values(created_at=datetime.now(UTC) - timedelta(seconds=10))
        )
        await session.commit()
    started = datetime.now(UTC) - timedelta(seconds=1)

    # The switch lands while the reply is still streaming…
    response = await two_model_client.patch(
        f"/api/v1/conversations/{conversation_id}", json={"model": SECOND_MODEL}
    )
    assert response.status_code == 200, response.text

    # …and the reply lands afterwards, stamped with the moment its stream began.
    await _persist_assistant_message(
        session_factory, uuid.uuid4(), conversation_id, "Answer from the old model", started
    )

    transcript = await _transcript(two_model_client, conversation_id)
    assert [(role, content.startswith("Model set to")) for role, content in transcript] == [
        ("user", False),
        ("assistant", False),
        ("system", True),
    ]


async def test_saving_the_model_a_conversation_already_has_writes_no_caption(
    two_model_app, two_model_client, session_factory
) -> None:
    conversation_id = await _seed(session_factory, model=SECOND_MODEL)
    _current_user(two_model_app)

    response = await two_model_client.patch(
        f"/api/v1/conversations/{conversation_id}", json={"model": SECOND_MODEL}
    )

    assert response.status_code == 200, response.text
    assert await _transcript(two_model_client, conversation_id) == []


async def test_a_model_the_deployment_no_longer_serves_falls_back(
    two_model_app, two_model_client, session_factory
) -> None:
    conversation_id = await _seed(
        session_factory, model=RETIRED_MODEL, messages=[("user", "Hello")]
    )
    _current_user(two_model_app)
    provider = _CapturingProvider()
    _use_provider(two_model_app, provider)

    await _send(two_model_client, conversation_id, "Still there?")

    # The retired id is never handed to a provider, and the substitution is
    # disclosed rather than silent.
    assert provider.models == [DEFAULT_MODEL]
    transcript = await _transcript(two_model_client, conversation_id)
    assert [role for role, _ in transcript] == ["user", "user", "system", "assistant"]
    assert RETIRED_MODEL in transcript[2][1]
    assert DEFAULT_MODEL in transcript[2][1]
    assert await _stored_model(session_factory, conversation_id) == DEFAULT_MODEL

    # Disclosed once, not on every turn.
    await _send(two_model_client, conversation_id, "And once more")

    roles = [role for role, _ in await _transcript(two_model_client, conversation_id)]
    assert roles.count("system") == 1
    assert provider.models == [DEFAULT_MODEL, DEFAULT_MODEL]


async def test_a_model_the_deployment_does_not_serve_is_refused_on_create(app, client) -> None:
    _current_user(app)

    response = await client.post("/api/v1/conversations", json={"model": RETIRED_MODEL})

    assert response.status_code == 422
    assert response.json()["code"] == "UNKNOWN_MODEL"


async def test_a_model_the_deployment_does_not_serve_is_refused_on_patch(
    app, client, session_factory
) -> None:
    conversation_id = await _seed(session_factory)
    _current_user(app)

    response = await client.patch(
        f"/api/v1/conversations/{conversation_id}", json={"model": RETIRED_MODEL}
    )

    assert response.status_code == 422
    assert response.json()["code"] == "UNKNOWN_MODEL"
    assert await _stored_model(session_factory, conversation_id) is None
    assert await _transcript(client, conversation_id) == []


async def test_a_new_conversation_keeps_the_model_it_was_given(
    two_model_app, two_model_client
) -> None:
    _current_user(two_model_app)

    response = await two_model_client.post("/api/v1/conversations", json={"model": SECOND_MODEL})

    assert response.status_code == 201, response.text
    assert response.json()["model"] == SECOND_MODEL


async def test_another_accounts_instructions_are_not_used(app, client, session_factory) -> None:
    mine = await _seed(session_factory, user_id=OWNER, instructions=INSTRUCTIONS)
    theirs = await _seed(session_factory, user_id=OTHER)
    provider = _CapturingProvider()
    _use_provider(app, provider)

    _current_user(app, OTHER)
    await _send(client, theirs)

    assert provider.sent == [[("user", "Hello")]]

    _current_user(app, OWNER)
    await _send(client, mine)

    assert provider.sent[1] == [("system", INSTRUCTIONS), ("user", "Hello")]
