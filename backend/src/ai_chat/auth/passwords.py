"""Password screening: length, entropy, and breach data (FR-2, ADR-0038).

Three checks behind one validator, run before the account exists:

1. length — the SDK's own floor, re-checked here so the validator is
   self-contained;
2. entropy and commonness — `zxcvbn` scores a password 0–4, and its bundled
   dictionaries are the "common patterns" data, so no list is maintained here.
   Its own scoring stops at 72 characters, so a longer passphrase is scored on
   its prefix rather than refused;
3. breach data — the HIBP range API, queried without the password ever leaving
   the server.

The last one is an external dependency, so it degrades the way the rate limiter
does (ADR-0020): a failure is logged and the password is accepted on the first
two checks rather than making sign-up unavailable (ADR-0038).
"""

from __future__ import annotations

import hashlib
import logging
from typing import Protocol, runtime_checkable

import httpx
from zxcvbn import zxcvbn

from ai_chat.auth.exceptions import WeakPasswordError
from ai_chat.shared.config import Settings, get_settings

logger = logging.getLogger(__name__)

MIN_LENGTH = 8

# `zxcvbn` raises on input longer than this instead of scoring a prefix, and a
# long passphrase is a legitimate choice, so the score is taken from the first
# 72 characters. The breach check still hashes the whole password.
ZXCVBN_MAX_LENGTH = 72
_HIBP_RANGE_URL = "https://api.pwnedpasswords.com/range/{prefix}"


@runtime_checkable
class PasswordBreachClient(Protocol):
    """Breached-password data, behind a port so tests need no network.

    The lookup is by hash prefix, never by password: the caller sends five
    hexadecimal characters and gets back the hash suffixes the breach data
    knows for them (ADR-0038).
    """

    async def known_suffixes(self, sha1_prefix: str) -> set[str]:
        """Upper-case hexadecimal suffixes recorded for a five-character prefix."""
        ...


class HibpRangeClient:
    """The HIBP range API over HTTP (ADR-0038).

    The password never leaves the server: only the first five characters of its
    SHA-1 hash are sent, and the response is a list of suffixes that match it.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def known_suffixes(self, sha1_prefix: str) -> set[str]:
        headers = {}
        if self._settings.hibp_api_key:
            # Optional, and only for rate headroom; the API is free without it.
            headers["hibp-api-key"] = self._settings.hibp_api_key

        async with httpx.AsyncClient(timeout=self._settings.hibp_timeout_seconds) as client:
            response = await client.get(
                _HIBP_RANGE_URL.format(prefix=sha1_prefix),
                headers=headers,
            )
            response.raise_for_status()
        return _parse_suffixes(response.text)


def _parse_suffixes(body: str) -> set[str]:
    """The suffixes in a range response, which is one ``SUFFIX:COUNT`` per line.

    A zero count means "not breached" — HIBP pads responses with such lines
    when asked to — so the count decides inclusion rather than the line merely
    being present.
    """
    suffixes: set[str] = set()
    for line in body.splitlines():
        suffix, _, count = line.strip().partition(":")
        if suffix and count.strip() not in ("", "0"):
            suffixes.add(suffix.upper())
    return suffixes


def split_sha1(password: str) -> tuple[str, str]:
    """The (prefix, suffix) pair the range API is queried with."""
    digest = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    return digest[:5], digest[5:]


async def validate_password(
    password: str,
    *,
    settings: Settings | None = None,
    breach_client: PasswordBreachClient | None = None,
) -> None:
    """Refuse a password that is too short, too weak, or already breached.

    Raises ``WeakPasswordError`` whose detail is the reason the form shows. The
    breach check runs last, because it is the only one that can fail for reasons
    other than the password itself, and a failure there is not the user's fault:
    it is logged and the password passes on length and entropy.
    """
    settings = settings or get_settings()

    if len(password) < MIN_LENGTH:
        raise WeakPasswordError(f"Password must be at least {MIN_LENGTH} characters.")

    score = zxcvbn(password[:ZXCVBN_MAX_LENGTH])["score"]
    if score < settings.password_min_score:
        raise WeakPasswordError(
            "Password is too easy to guess. Use a longer phrase, without common "
            "words, names, or keyboard patterns."
        )

    if not settings.password_breach_check_enabled:
        return

    client = breach_client or HibpRangeClient(settings)
    prefix, suffix = split_sha1(password)
    try:
        breached = await client.known_suffixes(prefix)
    except Exception:
        logger.warning(
            "Password breach check unavailable; accepting on length and entropy",
            exc_info=True,
        )
        return

    if suffix in breached:
        raise WeakPasswordError(
            "This password has appeared in a known data breach. Choose a different one."
        )
