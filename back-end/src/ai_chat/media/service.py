"""Fetch an external image under SSRF guards.

The guard order is the contract (ADR-0051):

1. parse and require ``http``/``https`` (no credentials, no fragments);
2. reject a host that is literally a private, loopback, link-local,
   multicast, reserved, or cloud-metadata address;
3. resolve DNS and reject the whole answer if *any* address is non-public;
4. connect to a validated IP, carrying the original ``Host`` header, so a
   rebinding answer cannot redirect the connection after validation;
5. follow at most ``max_redirects`` redirects, re-running every check per hop;
6. require an image content type;
7. stream with a byte cap abort (the cap is applied to the decompressed body).
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

import httpx

from ai_chat.media.exceptions import MediaFetchError
from ai_chat.shared.config import Settings

ALLOWED_SCHEMES = frozenset({"http", "https"})
ALLOWED_CONTENT_TYPES = frozenset({"image/png", "image/jpeg", "image/gif", "image/webp"})

# Cloud metadata endpoints, listed explicitly because several of them are not
# covered by ``ipaddress``'s private ranges on every interpreter.
_METADATA_ADDRESSES = frozenset(
    {"169.254.169.254", "100.100.100.200", "192.0.0.192", "fd00:ec2::254"}
)
# Carrier-grade NAT (RFC 6598) is not ``is_private`` in ``ipaddress``.
_BLOCKED_NETWORKS = (ipaddress.ip_network("100.64.0.0/10"),)

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address


@dataclass(frozen=True, slots=True)
class FetchedImage:
    content: bytes
    content_type: str


class AddressResolver(Protocol):
    """Resolves a host to one validated, connectable IP address."""

    async def resolve(self, host: str, port: int) -> str: ...


def normalise_ip(value: str) -> IPAddress:
    """Parse an address, folding IPv4-mapped IPv6 back to IPv4.

    Without the fold, ``::ffff:10.0.0.1`` would slip past the IPv4 private
    checks that ``ipaddress`` applies to the mapped form only after unwrapping.
    """
    try:
        address = ipaddress.ip_address(value.split("%", 1)[0])
    except ValueError as exc:
        raise MediaFetchError("Media URL host is not a valid address") from exc
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None:
        return address.ipv4_mapped
    return address


def ip_is_public(address: IPAddress) -> bool:
    if str(address) in _METADATA_ADDRESSES:
        return False
    if any(address in network for network in _BLOCKED_NETWORKS):
        return False
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def validate_url(url: httpx.URL) -> httpx.URL:
    if url.scheme not in ALLOWED_SCHEMES:
        raise MediaFetchError("Only http and https media URLs are allowed")
    if not url.host:
        raise MediaFetchError("Media URL has no host")
    if url.username or url.password:
        raise MediaFetchError("Media URL must not carry credentials")
    return url


def parse_url(raw: str) -> httpx.URL:
    try:
        url = httpx.URL(raw)
    except (httpx.InvalidURL, ValueError) as exc:
        raise MediaFetchError("Media URL could not be parsed") from exc
    return validate_url(url)


def check_literal_address(host: str) -> None:
    """Reject a host that is itself a non-public IP literal."""
    try:
        address = normalise_ip(host.strip("[]"))
    except MediaFetchError:
        return  # not a literal; the DNS answer is checked instead
    if not ip_is_public(address):
        raise MediaFetchError("Media URL host is a non-public address")


def _lookup(host: str, port: int) -> list[tuple]:
    return socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)


class DnsAddressResolver:
    """Resolves a host, rejecting the whole answer if any address is private."""

    def __init__(self, lookup: object = _lookup) -> None:
        self._lookup = lookup

    async def resolve(self, host: str, port: int) -> str:
        loop = asyncio.get_running_loop()
        try:
            infos = await loop.run_in_executor(None, self._lookup, host, port)
        except socket.gaierror as exc:
            raise MediaFetchError("Media URL host could not be resolved") from exc
        return _first_public_address(infos)


def _first_public_address(infos: Iterable[tuple]) -> str:
    resolved: list[str] = []
    for info in infos:
        address = info[4][0]
        normalised = normalise_ip(address)
        if not ip_is_public(normalised):
            raise MediaFetchError("Media URL resolves to a non-public address")
        resolved.append(str(normalised))
    if not resolved:
        raise MediaFetchError("Media URL host could not be resolved")
    return resolved[0]


def build_media_client(settings: Settings) -> httpx.AsyncClient:
    """A dedicated client for the proxy: no cookies, no credentials, no env.

    ``trust_env=False`` keeps proxy environment variables and ``.netrc`` out of
    the fetch, so the connection always goes where the guards decided.
    """
    return httpx.AsyncClient(
        timeout=settings.media_timeout_seconds,
        follow_redirects=False,
        cookies=None,
        trust_env=False,
    )


def _host_header(url: httpx.URL) -> str:
    host = url.host
    if ":" in host:  # IPv6 literal
        host = f"[{host}]"
    default_port = 443 if url.scheme == "https" else 80
    if url.port is not None and url.port != default_port:
        return f"{host}:{url.port}"
    return host


async def _send_pinned(client: httpx.AsyncClient, url: httpx.URL, address: str) -> httpx.Response:
    """GET ``url`` from ``address`` while preserving the original host identity."""
    headers = {"Host": _host_header(url)}
    extensions: dict[str, str] = {}
    if url.scheme == "https":
        # SNI and certificate verification use the original name, not the IP.
        extensions["sni_hostname"] = url.host
    request = client.build_request(
        "GET",
        url.copy_with(host=address),
        headers=headers,
        extensions=extensions or None,
    )
    try:
        return await client.send(request, stream=True, follow_redirects=False)
    except httpx.HTTPError as exc:
        raise MediaFetchError("Media fetch failed") from exc


async def _read_body(response: httpx.Response, max_bytes: int) -> bytes:
    """Read the decoded body, aborting the moment it exceeds the cap.

    ``aiter_bytes`` yields decompressed data, so a compressed body that inflates
    past the cap is stopped here rather than after it has been buffered whole.
    """
    chunks: list[bytes] = []
    total = 0
    async for chunk in response.aiter_bytes():
        total += len(chunk)
        if total > max_bytes:
            raise MediaFetchError("Media response exceeds the size limit")
        chunks.append(chunk)
    return b"".join(chunks)


def _image_content_type(response: httpx.Response) -> str:
    raw = response.headers.get("content-type", "")
    media_type = raw.split(";", 1)[0].strip().lower()
    if media_type not in ALLOWED_CONTENT_TYPES:
        raise MediaFetchError("Origin did not return a supported image type")
    return media_type


async def fetch_image(
    client: httpx.AsyncClient,
    raw_url: str,
    *,
    resolver: AddressResolver,
    max_bytes: int,
    max_redirects: int,
) -> FetchedImage:
    url = parse_url(raw_url)
    redirects = 0
    while True:
        check_literal_address(url.host)
        default_port = 443 if url.scheme == "https" else 80
        address = await resolver.resolve(url.host, url.port or default_port)
        response = await _send_pinned(client, url, address)
        try:
            if response.is_redirect:
                if redirects >= max_redirects:
                    raise MediaFetchError("Media request exceeded the redirect limit")
                location = response.headers.get("location")
                if not location:
                    raise MediaFetchError("Media redirect had no location")
                redirects += 1
                url = validate_url(url.join(location))
                continue
            if not response.is_success:
                raise MediaFetchError("Origin returned an error status")
            content_type = _image_content_type(response)
            content = await _read_body(response, max_bytes)
            return FetchedImage(content=content, content_type=content_type)
        finally:
            await response.aclose()
