"""In-process TTL cache for proxied images.

Single process by design (ADR-0051); acceptable at this scale. Entries are
keyed by the original URL and evicted by expiry or, when the total would be
exceeded, oldest-first.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

DEFAULT_MAX_BYTES = 64 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class CachedImage:
    content: bytes
    content_type: str


class ImageCache:
    def __init__(self, *, max_bytes: int = DEFAULT_MAX_BYTES, ttl_seconds: int) -> None:
        self._max_bytes = max_bytes
        # A single entry may never fill the whole cache, so one large image
        # cannot flush every other entry.
        self._max_entry_bytes = max_bytes // 2
        self._ttl_seconds = ttl_seconds
        self._entries: dict[str, tuple[float, CachedImage]] = {}
        self._total_bytes = 0

    def get(self, url: str) -> CachedImage | None:
        entry = self._entries.get(url)
        if entry is None:
            return None
        expires_at, image = entry
        if expires_at <= time.monotonic():
            self._drop(url)
            return None
        return image

    def set(self, url: str, image: CachedImage) -> None:
        size = len(image.content)
        if size > self._max_entry_bytes:
            return
        self._drop(url)
        self._entries[url] = (time.monotonic() + self._ttl_seconds, image)
        self._total_bytes += size
        self._prune()

    def _drop(self, url: str) -> None:
        entry = self._entries.pop(url, None)
        if entry is not None:
            self._total_bytes -= len(entry[1].content)

    def _prune(self) -> None:
        now = time.monotonic()
        expired = [url for url, (expires_at, _) in self._entries.items() if expires_at <= now]
        for url in expired:
            self._drop(url)
        for url in list(self._entries):  # insertion order == oldest first
            if self._total_bytes <= self._max_bytes:
                break
            self._drop(url)
