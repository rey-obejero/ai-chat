"""Composing the account's system prompt (FR-24, FR-25)."""

import logging

import pytest

from ai_chat.llm import PROMPT_MAX_CHARS, STYLE_FRAGMENTS, ResponseStyle, build_system_prompt

OTHER_STYLES = [style for style in ResponseStyle if style is not ResponseStyle.DEFAULT]


def test_the_fragments_cover_exactly_the_five_styles() -> None:
    # A style with no fragment, or a fragment no style can reach, is not a
    # state this module allows.
    assert set(STYLE_FRAGMENTS) == set(ResponseStyle)
    assert STYLE_FRAGMENTS[ResponseStyle.DEFAULT] == ""


@pytest.mark.parametrize("style", OTHER_STYLES)
def test_a_style_contributes_its_own_sentence(style: ResponseStyle) -> None:
    assert build_system_prompt(None, style) == STYLE_FRAGMENTS[style]


@pytest.mark.parametrize("style", OTHER_STYLES)
def test_the_fragment_is_reachable_by_its_stored_string(style: ResponseStyle) -> None:
    # The column holds the value, not the member, so the lookup has to work
    # from what the database returns.
    assert build_system_prompt(None, str(style)) == STYLE_FRAGMENTS[style]


def test_nothing_asked_for_yields_no_prompt() -> None:
    assert build_system_prompt(None, "default") is None
    assert build_system_prompt("   ", "default") is None


def test_instructions_lead_and_the_style_closes() -> None:
    prompt = build_system_prompt("Answer in British English.", "concise")

    assert prompt == f"Answer in British English.\n\n{STYLE_FRAGMENTS[ResponseStyle.CONCISE]}"


def test_instructions_are_trimmed() -> None:
    assert build_system_prompt("  Be brief.  ", "default") == "Be brief."


def test_an_unknown_style_adds_nothing() -> None:
    # Unreachable through the API — the enum guards the column — so this is a
    # guard against a stored value from somewhere else, not a supported path.
    assert build_system_prompt("Be brief.", "verbose") == "Be brief."


def test_a_prompt_over_the_cap_is_truncated_and_logged(caplog) -> None:
    instructions = "x" * (PROMPT_MAX_CHARS + 500)

    with caplog.at_level(logging.WARNING, logger="ai_chat.llm.prompts"):
        prompt = build_system_prompt(instructions, "concise")

    assert prompt is not None
    assert len(prompt) == PROMPT_MAX_CHARS
    assert prompt == "x" * PROMPT_MAX_CHARS
    assert "truncated" in caplog.text


def test_a_prompt_at_the_cap_is_left_alone(caplog) -> None:
    instructions = "x" * PROMPT_MAX_CHARS

    with caplog.at_level(logging.WARNING, logger="ai_chat.llm.prompts"):
        prompt = build_system_prompt(instructions, "default")

    assert prompt == instructions
    assert caplog.text == ""
