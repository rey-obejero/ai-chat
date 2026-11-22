"""Encoders for the AI SDK UI Message Stream protocol, version 1.

The protocol is Server-Sent Events whose data payloads are typed JSON parts,
terminated by a literal ``[DONE]`` marker. The exact shapes live here and
nowhere else, so a spec change is a one-file change with a guard test
(ADR-0012). See https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol.
"""

from __future__ import annotations

import json
from typing import Any

STREAM_HEADERS = {
    "cache-control": "no-cache",
    "x-vercel-ai-ui-message-stream": "v1",
    "x-accel-buffering": "no",
}

DONE = "data: [DONE]\n\n"


def _event(part: dict[str, Any] | str) -> str:
    data = part if isinstance(part, str) else json.dumps(part)
    return f"data: {data}\n\n"


def start(message_id: str) -> str:
    return _event({"type": "start", "messageId": message_id})


def text_start(text_id: str) -> str:
    return _event({"type": "text-start", "id": text_id})


def text_delta(text_id: str, delta: str) -> str:
    return _event({"type": "text-delta", "id": text_id, "delta": delta})


def text_end(text_id: str) -> str:
    return _event({"type": "text-end", "id": text_id})


def finish() -> str:
    return _event({"type": "finish"})


def error(error_text: str) -> str:
    return _event({"type": "error", "errorText": error_text})
