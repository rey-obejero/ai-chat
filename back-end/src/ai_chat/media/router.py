from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from ai_chat.auth import get_current_user_id
from ai_chat.media.cache import CachedImage, ImageCache
from ai_chat.media.exceptions import MediaFetchError
from ai_chat.media.service import (
    AddressResolver,
    DnsAddressResolver,
    build_media_client,
    fetch_image,
)
from ai_chat.shared.config import Settings

router = APIRouter(prefix="/media", tags=["media"])


def _settings(request: Request) -> Settings:
    return request.app.state.settings


def get_media_client(request: Request) -> httpx.AsyncClient:
    state = request.app.state
    client = getattr(state, "media_client", None)
    if client is None:
        client = build_media_client(_settings(request))
        state.media_client = client
    return client


def get_media_cache(request: Request) -> ImageCache:
    state = request.app.state
    cache = getattr(state, "media_cache", None)
    if cache is None:
        cache = ImageCache(ttl_seconds=_settings(request).media_cache_ttl_seconds)
        state.media_cache = cache
    return cache


def get_media_resolver(request: Request) -> AddressResolver:
    state = request.app.state
    resolver = getattr(state, "media_resolver", None)
    if resolver is None:
        resolver = DnsAddressResolver()
        state.media_resolver = resolver
    return resolver


def _image_response(image: CachedImage, settings: Settings) -> Response:
    return Response(
        content=image.content,
        # Never echo the origin's header: only our validated allowlist value.
        media_type=image.content_type,
        headers={
            "Cache-Control": f"private, max-age={settings.media_cache_ttl_seconds}",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/image")
async def read_image(
    url: str,
    request: Request,
    _user_id: str = Depends(get_current_user_id),
    client: httpx.AsyncClient = Depends(get_media_client),
    cache: ImageCache = Depends(get_media_cache),
    resolver: AddressResolver = Depends(get_media_resolver),
) -> Response:
    """Proxy an external image. Authenticated only — never an open proxy."""
    settings = _settings(request)
    cached = cache.get(url)
    if cached is not None:
        return _image_response(cached, settings)
    try:
        image = await fetch_image(
            client,
            url,
            resolver=resolver,
            max_bytes=settings.media_max_bytes,
            max_redirects=settings.media_max_redirects,
        )
    except MediaFetchError:
        return Response(status_code=502)
    cache.set(url, CachedImage(content=image.content, content_type=image.content_type))
    return _image_response(CachedImage(image.content, image.content_type), settings)
