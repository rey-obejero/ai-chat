"""Deriving and filtering display names (FR-7, ADR-0045).

The rules under test are the ones an account meets: the derived default is never
blank, and a name of the account's own is checked — composed, trimmed, capped,
and refused rather than rewritten when it will not do.
"""

import unicodedata

import pytest

from ai_chat.auth.display_name import (
    FALLBACK_DISPLAY_NAME,
    MAX_DISPLAY_NAME_LENGTH,
    contains_profanity,
    derive_display_name,
    validate_display_name,
)
from ai_chat.auth.exceptions import InvalidDisplayNameError

CAP = MAX_DISPLAY_NAME_LENGTH


def test_the_derivation_is_the_email_local_part_verbatim() -> None:
    assert derive_display_name("Amara.Okafor@example.com") == "Amara.Okafor"


def test_social_sign_in_derives_from_the_email_not_the_provider() -> None:
    # ADR-0045's alternative: the provider's own name is never used, and the
    # address is the one thing both sign-in paths have.
    assert derive_display_name("amara.okafor@gmail.com") == "amara.okafor"


def test_the_derivation_is_truncated_to_the_cap() -> None:
    derived = derive_display_name(f"{'a' * 80}@example.com")

    assert derived == "a" * CAP
    assert len(derived) == CAP


def test_a_truncation_that_lands_on_a_space_is_trimmed() -> None:
    # Truncating mid-name can leave the trailing space; the stored name carries
    # no surrounding whitespace.
    derived = derive_display_name(f"{'a' * (CAP - 1)} b@example.com")

    assert derived == "a" * (CAP - 1)


def test_the_derivation_is_stored_composed() -> None:
    derived = derive_display_name("Jose\u0301@example.com")

    assert derived == "José"
    assert unicodedata.is_normalized("NFC", derived)


def test_an_email_without_a_usable_local_part_falls_back() -> None:
    # Never blank (decision 1): the prompt offers a better name, but until then
    # the account still has one.
    assert derive_display_name("@example.com") == FALLBACK_DISPLAY_NAME
    assert derive_display_name("   @example.com") == FALLBACK_DISPLAY_NAME
    assert derive_display_name("") == FALLBACK_DISPLAY_NAME


def test_a_profane_local_part_falls_back_only_at_creation() -> None:
    # The derived name cannot be refused — there is nobody to answer a 422 at
    # account creation — so it falls back; the account's own name is refused
    # instead (see the validation tests below).
    assert derive_display_name("shit@example.com") == FALLBACK_DISPLAY_NAME
    with pytest.raises(InvalidDisplayNameError):
        validate_display_name("shit")


def test_a_long_local_part_that_is_profane_after_truncation_still_falls_back() -> None:
    # The filter judges what would be stored, not the whole address.
    assert derive_display_name(f"shit-{'a' * 60}@example.com") == FALLBACK_DISPLAY_NAME
    # ...and a word with no boundary after it is not that word: the truncated
    # form here is `shitshitshit…`, which is not `shit` on its own.
    assert derive_display_name(f"{'shit' * 20}@example.com") == "shit" * 12 + "sh"


def test_a_word_inside_a_longer_word_is_not_profanity() -> None:
    # Word boundaries, not substrings: these are names, not fragments.
    assert validate_display_name("Assassin") == "Assassin"
    assert validate_display_name("Scunthorpe") == "Scunthorpe"
    assert contains_profanity("Assassin") is False


def test_profanity_is_matched_case_insensitively_on_word_boundaries() -> None:
    assert contains_profanity("shIT happens") is True
    assert validate_display_name("Amara Okafor") == "Amara Okafor"


def test_a_leet_speak_substitution_is_folded() -> None:
    for spelling in ("Sh1t", "FUCK", "a$$hole", "b1tch"):
        assert contains_profanity(spelling) is True, spelling


def test_an_accented_spelling_is_folded_for_the_check() -> None:
    assert contains_profanity("shít") is True


def test_an_invisible_character_cannot_hide_a_profanity() -> None:
    assert contains_profanity("sh\u200bit") is True


def test_a_name_is_trimmed_before_it_is_measured() -> None:
    assert validate_display_name(f"  {'x' * CAP}  ") == "x" * CAP


def test_the_stored_name_is_nfc_composed() -> None:
    # Review finding L3: the checked value and the stored value are the same
    # string, and that string is composed.
    stored = validate_display_name("  Jose\u0301  ")

    assert stored == "José"
    assert unicodedata.is_normalized("NFC", stored)


def test_an_empty_name_is_refused() -> None:
    with pytest.raises(InvalidDisplayNameError, match="required"):
        validate_display_name("")


def test_a_whitespace_only_name_is_refused() -> None:
    with pytest.raises(InvalidDisplayNameError, match="required"):
        validate_display_name("   \t\n  ")


def test_a_name_over_the_cap_is_refused() -> None:
    with pytest.raises(InvalidDisplayNameError, match=f"at most {CAP} characters"):
        validate_display_name("x" * (CAP + 1))


def test_control_characters_are_refused() -> None:
    for name in ("Amara\x00Okafor", "Amara\nOkafor", "Amara\tOkafor"):
        with pytest.raises(InvalidDisplayNameError, match="control characters"):
            validate_display_name(name)


def test_a_profane_name_is_refused_with_a_readable_reason() -> None:
    # Refused, not masked: the account is told why and keeps its old name.
    with pytest.raises(InvalidDisplayNameError, match="not allowed"):
        validate_display_name("Amara Fuck Okafor")
