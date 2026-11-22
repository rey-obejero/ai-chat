"""One logging configuration, with the request's identifier on every line."""

from __future__ import annotations

import logging
from contextvars import ContextVar, Token

from ai_chat.shared.config import Settings

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s"


class RequestIdFilter(logging.Filter):
    """Fill in the request id for records emitted outside a request."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_var.get()
        return True


def configure_logging(settings: Settings) -> None:
    """Configure the root logger once per process.

    ``basicConfig`` is a no-op when the root logger already has handlers, which
    keeps repeated ``create_app`` calls in tests harmless and leaves pytest's
    log capture alone.
    """
    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    logging.basicConfig(
        level=settings.log_level.upper(),
        format=LOG_FORMAT,
        handlers=[handler],
    )


def set_request_id(value: str) -> Token[str]:
    return request_id_var.set(value)
