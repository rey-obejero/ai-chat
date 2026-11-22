import socket
import threading
import time
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from httpx import ASGITransport, AsyncClient

from ai_chat.auth import get_current_user_id
from ai_chat.main import create_app
from ai_chat.shared.config import Settings
from ai_chat.shared.exceptions import NotAuthenticatedError

# A 1x1 PNG.
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000a49444154789c6360000002000154a24f5f0000000049454e44ae426082"
)


class _StaticResolver:
    async def resolve(self, host: str, port: int) -> str:
        return "127.0.0.1"


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    counts: Counter[str] = Counter()

    def do_GET(self) -> None:  # noqa: N802
        type(self).counts[self.path] += 1
        if self.path == "/image.png":
            self._respond(200, "image/png", PNG)
        elif self.path == "/redirect-private":
            self.send_response(302)
            self.send_header("Location", "http://10.0.0.5/secret.png")
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif self.path == "/not-an-image":
            self._respond(200, "text/html", b"<html></html>")
        elif self.path == "/bad-redirect":
            self.send_response(302)
            # Not a parsable URL: this makes `httpx` raise `InvalidURL`, which is
            # not an `HTTPError`, so it used to escape as a 500.
            self.send_header("Location", "http://[not-an-ipv6]/x.png")
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif self.path == "/trickle.png":
            # Every write lands inside `httpx`'s per-read timeout and the promised
            # body never arrives, so only a whole-fetch deadline ends this.
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(1024 * 1024))
            self.end_headers()
            for _ in range(60):
                time.sleep(0.05)
                self.wfile.write(b"\x89PNG")
        else:
            self._respond(404, "text/plain", b"missing")

    def _respond(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture
def image_server():
    counts: Counter[str] = Counter()
    _Handler.counts = counts
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        yield f"http://localhost:{port}", counts
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def _current_user(app) -> None:
    async def override() -> str:
        return "user-1"

    app.dependency_overrides[get_current_user_id] = override


def _pin_resolver(app) -> None:
    app.state.media_resolver = _StaticResolver()


async def test_happy_path_png_round_trips(app, client, image_server) -> None:
    base, _counts = image_server
    _current_user(app)
    _pin_resolver(app)

    response = await client.get("/api/v1/media/image", params={"url": f"{base}/image.png"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "private, max-age=86400"
    assert response.content == PNG


async def test_redirect_to_a_private_address_fails(app, client, image_server) -> None:
    base, _counts = image_server
    _current_user(app)
    _pin_resolver(app)

    response = await client.get("/api/v1/media/image", params={"url": f"{base}/redirect-private"})

    assert response.status_code == 502
    assert response.content == b""


async def test_non_image_origin_returns_502(app, client, image_server) -> None:
    base, _counts = image_server
    _current_user(app)
    _pin_resolver(app)

    response = await client.get("/api/v1/media/image", params={"url": f"{base}/not-an-image"})

    assert response.status_code == 502
    assert response.content == b""


async def test_cache_hit_does_not_re_request_the_origin(app, client, image_server) -> None:
    base, counts = image_server
    _current_user(app)
    _pin_resolver(app)
    url = f"{base}/image.png"

    first = await client.get("/api/v1/media/image", params={"url": url})
    assert first.status_code == 200
    assert counts["/image.png"] == 1

    second = await client.get("/api/v1/media/image", params={"url": url})
    assert second.status_code == 200
    assert second.content == PNG
    # Served from the in-process cache: the origin was contacted exactly once.
    assert counts["/image.png"] == 1


async def test_unauthenticated_callers_get_401(app, client, image_server) -> None:
    base, _counts = image_server

    async def unauthenticated() -> str:
        raise NotAuthenticatedError("No session cookie")

    app.dependency_overrides[get_current_user_id] = unauthenticated

    response = await client.get("/api/v1/media/image", params={"url": f"{base}/image.png"})

    assert response.status_code == 401


async def test_disabled_proxy_is_absent(session_factory) -> None:
    application = create_app(
        Settings(
            _env_file=None,
            rate_limit_enabled=False,
            token_quota_enabled=False,
            media_proxy_enabled=False,
        ),
        init_auth=False,
    )
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        response = await http_client.get(
            "/api/v1/media/image", params={"url": "http://example.com/x.png"}
        )

    assert response.status_code == 404


async def test_unknown_host_is_resolved_then_rejected(monkeypatch) -> None:
    # The default resolver rejects a DNS answer that points at a private
    # address; nothing in the request path bypasses it.
    def lookup(host: str, port: int, **kwargs: object) -> list[tuple]:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))]

    monkeypatch.setattr(socket, "getaddrinfo", lookup)

    application = create_app(
        Settings(_env_file=None, rate_limit_enabled=False, token_quota_enabled=False),
        init_auth=False,
    )
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        application.dependency_overrides[get_current_user_id] = _make_user_override()
        response = await http_client.get(
            "/api/v1/media/image", params={"url": "http://blocked.example/image.png"}
        )

    assert response.status_code == 502


def _make_user_override():
    async def override() -> str:
        return "user-1"

    return override


async def test_an_unparseable_redirect_location_is_a_502(app, client, image_server) -> None:
    base, _counts = image_server
    _current_user(app)
    _pin_resolver(app)

    response = await client.get("/api/v1/media/image", params={"url": f"{base}/bad-redirect"})

    assert response.status_code == 502
    assert response.content == b""


async def test_a_trickling_origin_is_cut_off_by_the_deadline(image_server) -> None:
    base, _counts = image_server
    application = create_app(
        Settings(
            _env_file=None,
            rate_limit_enabled=False,
            token_quota_enabled=False,
            media_timeout_seconds=0.2,
        ),
        init_auth=False,
    )
    transport = ASGITransport(app=application)
    started = time.monotonic()
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        application.dependency_overrides[get_current_user_id] = _make_user_override()
        application.state.media_resolver = _StaticResolver()
        response = await http_client.get(
            "/api/v1/media/image", params={"url": f"{base}/trickle.png"}
        )
    elapsed = time.monotonic() - started

    assert response.status_code == 502
    # Ended by the deadline, not by the origin finishing three seconds later.
    assert elapsed < 1.5, f"the fetch took {elapsed:.2f}s"
