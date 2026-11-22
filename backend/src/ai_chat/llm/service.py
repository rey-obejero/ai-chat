from functools import lru_cache

from openai import AsyncOpenAI

from ai_chat.llm.adapters.openai import OpenAIChatProvider
from ai_chat.llm.exceptions import LLMNotConfiguredError
from ai_chat.llm.port import ChatProvider
from ai_chat.shared.config import Settings, get_settings


def build_chat_provider(settings: Settings) -> ChatProvider:
    """Construct the provider from configuration.

    Raises ``LLMNotConfiguredError`` rather than failing at import time, so the
    rest of the API still runs without a key (BYOK lands here later, ADR-0019).
    """
    if not settings.llm_api_key:
        raise LLMNotConfiguredError(detail="No language model API key is configured.")

    client = AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        timeout=settings.llm_request_timeout,
        default_headers={
            "HTTP-Referer": settings.frontend_url,
            "X-Title": settings.app_name,
        },
    )
    return OpenAIChatProvider(
        client,
        model=settings.llm_model,
        max_output_tokens=settings.llm_max_output_tokens,
    )


@lru_cache
def get_chat_provider() -> ChatProvider:
    """Process-wide provider, resolvable as a FastAPI dependency."""
    return build_chat_provider(get_settings())
