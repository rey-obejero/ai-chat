"""Deriving and validating display names (FR-7, ADR-0045).

Every account carries a name from the moment it exists, so no code path has to
render a nameless account: the derivation below takes the email's local part.
A name the account supplies itself is checked here and refused when it is not
usable — never silently rewritten, because a masked or renamed name is a
surprise the account cannot see coming.

The bundled list is English-centric. The FRD's open question about names in
other scripts is recorded there and is unchanged by this module.
"""

from __future__ import annotations

import re
import unicodedata

from ai_chat.auth.exceptions import InvalidDisplayNameError

# The column's width and the cap on a name (FR-7).
MAX_DISPLAY_NAME_LENGTH = 50

# What an account is called when nothing usable can be derived — an empty local
# part, or one the filter refuses. The prompt then offers the account a better
# name; until then this is still a name, which is the point.
FALLBACK_DISPLAY_NAME = "User"

# Curated, English-centric and deliberately short: the list is a product
# decision about names, not a general content filter. Word boundaries in
# `_PROFANITY_PATTERN` are what keep "assassin" and "Scunthorpe" out of it.
_PROFANITY = (
    "ass",
    "asshole",
    "bastard",
    "bitch",
    "bollocks",
    "chink",
    "coon",
    "cunt",
    "damn",
    "dick",
    "douche",
    "dyke",
    "fag",
    "faggot",
    "fuck",
    "goddamn",
    "jackass",
    "kike",
    "nigga",
    "nigger",
    "piss",
    "prick",
    "pussy",
    "retard",
    "shit",
    "slut",
    "spastic",
    "spic",
    "tranny",
    "twat",
    "wanker",
    "whore",
    "wog",
)

_PROFANITY_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(word) for word in _PROFANITY) + r")\b",
    re.IGNORECASE,
)

# The "small leetspeak fold": the substitutions people actually write.
_LEET_FOLD = str.maketrans(
    {
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
        "@": "a",
        "$": "s",
    }
)


def normalise_display_name(raw: str) -> str:
    """The name as it is checked and stored: NFC-composed, then trimmed.

    Composing first is deliberate (review finding L3): the profanity check and
    the column then see the same string, so an accent typed decomposed cannot
    mean one thing to the filter and another to everyone else.
    """
    return unicodedata.normalize("NFC", raw).strip()


def _fold(name: str) -> str:
    """The name as the filter compares it.

    Accents, invisible characters and leetspeak are folded away, so `fück`,
    `f\\u200buck` and `f4ck` all read as `fuck`. Folding is for the comparison
    only; the stored name keeps every character it was given.

    Invisible characters are folded rather than refused: some scripts need them
    in a real name, and folding alone is enough to stop them hiding a profanity.
    """
    decomposed = unicodedata.normalize("NFD", name)
    plain = "".join(
        character for character in decomposed if unicodedata.category(character) not in {"Mn", "Cf"}
    )
    return plain.translate(_LEET_FOLD).casefold()


def contains_profanity(name: str) -> bool:
    """Whether the name matches the bundled list on word boundaries.

    Case-insensitively, over the folded form, so capitalisation, accents and
    substitutions do not get a profanity past the filter.
    """
    return _PROFANITY_PATTERN.search(_fold(normalise_display_name(name))) is not None


def validate_display_name(raw: str) -> str:
    """The form of a user-supplied name that may be stored, or a refusal.

    The rules, in one place for both the prompt and the settings field: NFC,
    trim, 1–50 characters, no control characters, and no profanity. The refusal
    says what is wrong; nothing is masked and nothing is silently renamed.
    """
    name = normalise_display_name(raw)
    if not name:
        raise InvalidDisplayNameError("A display name is required.")
    if len(name) > MAX_DISPLAY_NAME_LENGTH:
        raise InvalidDisplayNameError(
            f"A display name must be at most {MAX_DISPLAY_NAME_LENGTH} characters."
        )
    if any(unicodedata.category(character) == "Cc" for character in name):
        raise InvalidDisplayNameError("A display name may not contain control characters.")
    if contains_profanity(name):
        raise InvalidDisplayNameError("That display name is not allowed. Please choose another.")
    return name


def derive_display_name(email: str) -> str:
    """The name a new account starts with (FR-7, decision 1).

    The email's local part verbatim, truncated to the cap, then filtered. Social
    sign-in arrives here too, so the provider's own name is never used
    (ADR-0045). A local part that cannot be used at all — empty, or refused by
    the filter — falls back rather than leaving the account nameless; the
    prompt then invites the account to choose.
    """
    local_part = normalise_display_name(email.split("@", 1)[0])[:MAX_DISPLAY_NAME_LENGTH]
    try:
        return validate_display_name(local_part)
    except InvalidDisplayNameError:
        return FALLBACK_DISPLAY_NAME
