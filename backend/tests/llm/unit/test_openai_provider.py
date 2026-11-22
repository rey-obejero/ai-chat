from types import SimpleNamespace

import pytest
from openai import OpenAIError

from ai_chat.llm.adapters.openai import OpenAIChatProvider
from ai_chat.llm.exceptions import LLMProviderError
from ai_chat.llm.schemas import ChatMessage, Role


def _event(
    content: str = "",
    finish_reason: str | None = None,
    usage: SimpleNamespace | None = None,
    error: SimpleNamespace | None = None,
) -> SimpleNamespace:
    event = SimpleNamespace(
        choices=[
            SimpleNamespace(
                delta=SimpleNamespace(content=content),
                finish_reason=finish_reason,
            )
        ]
    )
    if usage is not None:
        event.usage = usage
    if error is not None:
        event.error = error
    return event


def _usage(prompt: int = 5, completion: int = 2) -> SimpleNamespace:
    return SimpleNamespace(
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=prompt + completion,
    )


class _FakeCompletions:
    """Stands in for ``client.chat.completions`` (ADR-0021)."""

    def __init__(self, events: list[SimpleNamespace], *, error: Exception | None = None) -> None:
        self._events = events
        self._error = error
        self.kwargs: dict[str, object] = {}

    async def create(self, **kwargs: object):
        self.kwargs = kwargs
        if self._error is not None:
            raise self._error

        async def stream():
            for event in self._events:
                yield event

        return stream()


class _FakeClient:
    def __init__(self, completions: _FakeCompletions) -> None:
        self.chat = SimpleNamespace(completions=completions)


def _provider(completions: _FakeCompletions, **kwargs: object) -> OpenAIChatProvider:
    client = _FakeClient(completions)
    return OpenAIChatProvider(client, model="openai/gpt-4o-mini", **kwargs)  # type: ignore[arg-type]


async def test_stream_chat_maps_deltas_and_finish() -> None:
    completions = _FakeCompletions([_event("Hel"), _event("lo"), _event(finish_reason="stop")])
    provider = _provider(completions)

    chunks = [
        chunk async for chunk in provider.stream_chat([ChatMessage(role=Role.USER, content="hi")])
    ]

    assert "".join(chunk.content for chunk in chunks) == "Hello"
    assert chunks[-1].finish_reason == "stop"


async def test_stream_chat_skips_empty_events() -> None:
    completions = _FakeCompletions([_event(), _event("ok", finish_reason="stop")])
    provider = _provider(completions)

    chunks = [
        chunk async for chunk in provider.stream_chat([ChatMessage(role=Role.USER, content="hi")])
    ]

    assert [chunk.content for chunk in chunks] == ["ok"]


async def test_stream_chat_sends_expected_payload() -> None:
    completions = _FakeCompletions([_event("ok", finish_reason="stop")])
    provider = _provider(completions, max_output_tokens=256)

    _ = [chunk async for chunk in provider.stream_chat([ChatMessage(role=Role.USER, content="hi")])]

    assert completions.kwargs["model"] == "openai/gpt-4o-mini"
    assert completions.kwargs["stream"] is True
    assert completions.kwargs["stream_options"] == {"include_usage": True}
    assert completions.kwargs["max_tokens"] == 256
    assert completions.kwargs["messages"] == [{"role": "user", "content": "hi"}]


async def test_stream_chat_allows_model_override() -> None:
    completions = _FakeCompletions([_event("ok", finish_reason="stop")])
    provider = _provider(completions)

    _ = [
        chunk
        async for chunk in provider.stream_chat(
            [ChatMessage(role=Role.USER, content="hi")], model="anthropic/claude-haiku"
        )
    ]

    assert completions.kwargs["model"] == "anthropic/claude-haiku"


async def test_provider_failure_becomes_domain_error() -> None:
    completions = _FakeCompletions([], error=OpenAIError("boom"))
    provider = _provider(completions)

    with pytest.raises(LLMProviderError):
        _ = [
            chunk
            async for chunk in provider.stream_chat([ChatMessage(role=Role.USER, content="hi")])
        ]


async def test_stream_chat_captures_token_usage() -> None:
    completions = _FakeCompletions([_event("ok"), _event(finish_reason="stop", usage=_usage())])
    provider = _provider(completions)

    chunks = [
        chunk async for chunk in provider.stream_chat([ChatMessage(role=Role.USER, content="hi")])
    ]

    assert chunks[-1].usage is not None
    assert chunks[-1].usage.total_tokens == 7


async def test_stream_chat_accepts_a_usage_only_final_chunk() -> None:
    # OpenAI proper reports usage on a chunk with an empty choices array.
    usage_only = SimpleNamespace(choices=[], usage=_usage())
    completions = _FakeCompletions([_event("ok"), usage_only])
    provider = _provider(completions)

    chunks = [
        chunk async for chunk in provider.stream_chat([ChatMessage(role=Role.USER, content="hi")])
    ]

    assert chunks[-1].usage is not None
    assert chunks[-1].usage.total_tokens == 7


async def test_stream_chat_treats_a_mid_stream_error_frame_as_a_failure() -> None:
    completions = _FakeCompletions(
        [
            _event("partial"),
            _event(
                finish_reason="error",
                error=SimpleNamespace(code="server_error", message="provider disconnected"),
            ),
        ]
    )
    provider = _provider(completions)

    with pytest.raises(LLMProviderError):
        _ = [
            chunk
            async for chunk in provider.stream_chat([ChatMessage(role=Role.USER, content="hi")])
        ]
