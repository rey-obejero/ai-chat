"""Prompt composition: the account's instructions, plus its style (FR-24, FR-25)."""

from __future__ import annotations

import logging
from enum import StrEnum

logger = logging.getLogger(__name__)

# The composed prompt's hard ceiling. The 2000-character cap on instructions
# and one sentence of style cannot reach it today; it is the bound that keeps a
# future, longer input (per-conversation options, a longer fragment) from
# growing the prompt without limit.
PROMPT_MAX_CHARS = 4000


class ResponseStyle(StrEnum):
    """How the assistant should sound. The vocabulary and its fragments are one
    unit of data: a style with no fragment, or a fragment with no style, is not
    a state this module allows."""

    DEFAULT = "default"
    CONCISE = "concise"
    DETAILED = "detailed"
    FORMAL = "formal"
    CASUAL = "casual"


# One fixed sentence per style. `default` adds nothing: the prompt is then the
# account's own words, which is what "no style chosen" has to mean.
STYLE_FRAGMENTS: dict[ResponseStyle, str] = {
    ResponseStyle.DEFAULT: "",
    ResponseStyle.CONCISE: (
        "Keep every reply short: answer directly, in plain sentences, without preamble."
    ),
    ResponseStyle.DETAILED: (
        "Give thorough replies: explain your reasoning, add context, and cover the "
        "cases that matter."
    ),
    ResponseStyle.FORMAL: (
        "Write in a formal, professional register: no slang, no exclamation marks, no contractions."
    ),
    ResponseStyle.CASUAL: "Write in a relaxed, friendly register, as if talking with a colleague.",
}


def build_system_prompt(instructions: str | None, style: str) -> str | None:
    """The one system message the account's settings produce, or ``None``.

    Instructions come first and the style fragment second, so the user's own
    words lead and the house style closes. Nothing to say yields ``None``
    rather than an empty message, because an empty prompt is not a prompt.
    """
    instructions = (instructions or "").strip()
    fragment = STYLE_FRAGMENTS.get(style, "")
    parts = [part for part in (instructions, fragment) if part]
    if not parts:
        return None

    prompt = "\n\n".join(parts)
    if len(prompt) > PROMPT_MAX_CHARS:
        logger.warning(
            "System prompt truncated to %s characters (instructions %s, fragment %s)",
            PROMPT_MAX_CHARS,
            len(instructions),
            len(fragment),
        )
        prompt = prompt[:PROMPT_MAX_CHARS]
    return prompt
