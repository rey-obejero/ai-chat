import socket

import httpx
import pytest

from ai_chat.media.exceptions import MediaFetchError
from ai_chat.media.service import (
    DnsAddressResolver,
    check_literal_address,
    fetch_image,
    parse_url,
)

PUBLIC_IP = "93.184.216.34"


class _StaticResolver:
    def __init__(self, address: str = PUBLIC_IP) -> None:
        self.address = address

    async def resolve(self, host: str, port: int) -> str:
        return self.address


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        follow_redirects=False,
        timeout=5.0,
    )


@pytest.mark.parametrize(
    "raw",
    [
        "ftp://example.com/x.png",
        "file:///etc/passwd",
        "data:image/png;base64,AAAA",
    ],
)
def test_parse_url_rejects_non_http_schemes(raw: str) -> None:
    with pytest.raises(MediaFetchError):
        parse_url(raw)


def test_parse_url_rejects_credentials() -> None:
    with pytest.raises(MediaFetchError):
        parse_url("http://user:secret@example.com/x.png")


@pytest.mark.parametrize(
    "host",
    [
        "10.0.0.1",  # private
        "172.16.5.4",  # private
        "192.168.1.1",  # private
        "127.0.0.1",  # loopback
        "::1",  # loopback
        "169.254.1.1",  # link-local
        "fe80::1",  # link-local
        "169.254.169.254",  # cloud metadata
        "100.100.100.200",  # cloud metadata
        "224.0.0.1",  # multicast
        "100.64.0.1",  # carrier-grade NAT
        "::ffff:10.0.0.1",  # IPv4-mapped private
        "::ffff:169.254.169.254",  # IPv4-mapped metadata
    ],
)
def test_check_literal_address_rejects_non_public(host: str) -> None:
    with pytest.raises(MediaFetchError):
        check_literal_address(host)


@pytest.mark.parametrize("host", ["93.184.216.34", "example.com", "::ffff:93.184.216.34"])
def test_check_literal_address_allows_public(host: str) -> None:
    check_literal_address(host)


async def test_dns_answer_with_private_address_is_rejected() -> None:
    def lookup(host: str, port: int) -> list[tuple]:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))]

    resolver = DnsAddressResolver(lookup=lookup)
    with pytest.raises(MediaFetchError):
        await resolver.resolve("example.com", 80)


async def test_dns_answer_with_any_private_address_is_rejected() -> None:
    def lookup(host: str, port: int) -> list[tuple]:
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", port)),
        ]

    resolver = DnsAddressResolver(lookup=lookup)
    with pytest.raises(MediaFetchError):
        await resolver.resolve("example.com", 80)


async def test_dns_answer_with_public_address_is_accepted() -> None:
    def lookup(host: str, port: int) -> list[tuple]:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    resolver = DnsAddressResolver(lookup=lookup)
    assert await resolver.resolve("example.com", 80) == "93.184.216.34"


async def test_non_image_content_type_is_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"Content-Type": "text/html"}, content=b"<html>")

    client = _client(handler)
    async with client:
        with pytest.raises(MediaFetchError):
            await fetch_image(
                client,
                "http://example.com/page",
                resolver=_StaticResolver(),
                max_bytes=1024,
                max_redirects=4,
            )


async def test_oversized_body_is_aborted_at_the_byte_cap() -> None:
    payload = b"\x89PNG" + b"x" * 4096

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"Content-Type": "image/png"}, content=payload)

    client = _client(handler)
    async with client:
        with pytest.raises(MediaFetchError):
            await fetch_image(
                client,
                "http://example.com/big.png",
                resolver=_StaticResolver(),
                max_bytes=1024,
                max_redirects=4,
            )


async def test_body_within_the_cap_is_returned() -> None:
    payload = b"\x89PNG-body"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"Content-Type": "image/png; charset=binary"}, content=payload
        )

    client = _client(handler)
    async with client:
        image = await fetch_image(
            client,
            "http://example.com/ok.png",
            resolver=_StaticResolver(),
            max_bytes=1024,
            max_redirects=4,
        )
    assert image.content == payload
    assert image.content_type == "image/png"


async def test_redirect_is_revalidated_per_hop() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers["host"])
        return httpx.Response(302, headers={"Location": "http://10.0.0.5/secret"})

    client = _client(handler)
    async with client:
        with pytest.raises(MediaFetchError):
            await fetch_image(
                client,
                "http://example.com/redirect",
                resolver=_StaticResolver(),
                max_bytes=1024,
                max_redirects=4,
            )
    # The private hop was rejected before a second request went out.
    assert seen == ["example.com"]


async def test_redirect_chain_up_to_the_limit_succeeds() -> None:
    payload = b"\x89PNG"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/0":
            return httpx.Response(302, headers={"Location": "http://example.com/1"})
        if request.url.path == "/1":
            return httpx.Response(302, headers={"Location": "http://example.com/2"})
        return httpx.Response(200, headers={"Content-Type": "image/png"}, content=payload)

    client = _client(handler)
    async with client:
        image = await fetch_image(
            client,
            "http://example.com/0",
            resolver=_StaticResolver(),
            max_bytes=1024,
            max_redirects=4,
        )
    assert image.content == payload


async def test_redirect_chain_is_capped_at_the_limit() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        return httpx.Response(302, headers={"Location": "http://example.com/next"})

    client = _client(handler)
    async with client:
        with pytest.raises(MediaFetchError):
            await fetch_image(
                client,
                "http://example.com/start",
                resolver=_StaticResolver(),
                max_bytes=1024,
                max_redirects=4,
            )
    # One initial request plus four followed redirects; the fifth redirect aborts.
    assert len(seen) == 5


async def test_redirect_to_non_http_scheme_is_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"Location": "ftp://example.com/x.png"})

    client = _client(handler)
    async with client:
        with pytest.raises(MediaFetchError):
            await fetch_image(
                client,
                "http://example.com/redirect",
                resolver=_StaticResolver(),
                max_bytes=1024,
                max_redirects=4,
            )
