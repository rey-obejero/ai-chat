"""Spec-drift guard for the AI SDK UI Message Stream protocol (ADR-0012)."""

import json

from ai_chat.shared import streaming as sse


def test_done_marker_is_the_literal_sentinel() -> None:
    assert sse.DONE == "data: [DONE]\n\n"


def test_text_delta_has_the_pinned_shape() -> None:
    assert (
        sse.text_delta("text_1", "Hello")
        == 'data: {"type": "text-delta", "id": "text_1", "delta": "Hello"}\n\n'
    )


def test_every_part_is_a_well_formed_sse_data_line() -> None:
    parts = [
        sse.start("msg_1"),
        sse.text_start("text_1"),
        sse.text_delta("text_1", "hi"),
        sse.text_end("text_1"),
        sse.finish(),
        sse.error("boom"),
    ]

    for part in parts:
        assert part.startswith("data: ")
        assert part.endswith("\n\n")
        assert part.count("\n") == 2
        parsed = json.loads(part.removeprefix("data: ").removesuffix("\n\n"))
        assert isinstance(parsed["type"], str)


def test_headers_pin_the_protocol_version() -> None:
    assert sse.STREAM_HEADERS["x-vercel-ai-ui-message-stream"] == "v1"
    assert sse.STREAM_HEADERS["cache-control"] == "no-cache"
