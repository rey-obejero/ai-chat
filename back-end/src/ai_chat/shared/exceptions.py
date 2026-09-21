from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

PROBLEM_JSON = "application/problem+json"


class AppError(Exception):
    """Base domain error. Service layer raises these; handlers serialize them."""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    code: str = "INTERNAL_ERROR"
    title: str = "Internal Server Error"

    def __init__(
        self,
        detail: str | None = None,
        *,
        code: str | None = None,
        status_code: int | None = None,
        title: str | None = None,
        extensions: dict[str, Any] | None = None,
    ) -> None:
        self.detail = detail or self.title
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        if title is not None:
            self.title = title
        self.extensions = extensions or {}
        super().__init__(self.detail)


class NotAuthenticatedError(AppError):
    status_code = HTTPStatus.UNAUTHORIZED
    code = "NOT_AUTHENTICATED"
    title = "Not Authenticated"


class NotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND
    code = "NOT_FOUND"
    title = "Not Found"


class RateLimitedError(AppError):
    status_code = HTTPStatus.TOO_MANY_REQUESTS
    code = "RATE_LIMITED"
    title = "Too Many Requests"


def problem_body(
    *,
    status_code: int,
    title: str,
    detail: str,
    code: str,
    instance: str,
    extensions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": instance,
        "code": code,
    }
    if extensions:
        body.update(extensions)
    return body


def problem_response(
    *,
    status_code: int,
    title: str,
    detail: str,
    code: str,
    instance: str,
    extensions: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=problem_body(
            status_code=status_code,
            title=title,
            detail=detail,
            code=code,
            instance=instance,
            extensions=extensions,
        ),
        media_type=PROBLEM_JSON,
        headers=headers,
    )


async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return problem_response(
        status_code=exc.status_code,
        title=exc.title,
        detail=exc.detail,
        code=exc.code,
        instance=request.url.path,
        extensions=exc.extensions,
    )


async def _validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        {
            "location": list(error.get("loc", [])),
            "message": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        for error in exc.errors()
    ]
    return problem_response(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        title="Unprocessable Entity",
        detail="Request validation failed.",
        code="VALIDATION_ERROR",
        instance=request.url.path,
        extensions={"errors": errors},
    )


async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    try:
        title = HTTPStatus(exc.status_code).phrase
    except ValueError:
        title = "Error"
    return problem_response(
        status_code=exc.status_code,
        title=title,
        detail=str(exc.detail),
        code=f"HTTP_{exc.status_code}",
        instance=request.url.path,
        headers=getattr(exc, "headers", None),
    )


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s", request.url.path, exc_info=exc)
    return problem_response(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        detail="An unexpected error occurred.",
        code="INTERNAL_ERROR",
        instance=request.url.path,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _unhandled_exception_handler)
