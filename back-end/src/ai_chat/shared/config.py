from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Chat"
    api_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    database_url: str = "postgresql+asyncpg://aichat:aichat@localhost:5433/aichat"

    supertokens_connection_uri: str = "http://localhost:3567"
    supertokens_api_key: str = ""

    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""

    # Transactional email over SMTP (ADR-0030). An empty `smtp_host` means mail
    # is unconfigured: the reset endpoint then fails loudly instead of silently
    # reporting success and sending nothing. Development catches mail in
    # Mailpit — `localhost` when the API runs on the host, `mailpit` in Compose.
    smtp_host: str = ""
    smtp_port: int = 1025
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_name: str = ""
    smtp_from_email: str = ""
    smtp_secure: bool = False

    # A stand-in identity provider for the end-to-end suite (ADR-0029). Off by
    # default, and deliberately not documented in `.env.example`: it is not a
    # setting anyone should reach for, and the point of the switch is that a
    # stray value cannot turn it on.
    #
    # Three things must hold before it is registered, and each is checked in
    # `_test_provider`: this switch, credentials for it, and a base URL on a
    # known local host. The last one is what stops a real deployment from being
    # pointed at an unverified provider by setting the other two.
    test_idp_enabled: bool = False
    test_idp_base_url: str = ""
    test_idp_client_id: str = ""
    test_idp_client_secret: str = ""

    # LLM provider — OpenRouter by default (ADR-0018). The key is env-only
    # (ADR-0009) and no default means a missing key fails loudly at request time.
    llm_api_key: str = ""
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "openai/gpt-4o-mini"
    llm_embedding_model: str = "openai/text-embedding-3-small"
    llm_max_output_tokens: int = 1024
    llm_request_timeout: float = 60.0

    # Rate limiting (ADR-0020). Memory storage in development; switch to
    # "async+redis://…" once the API runs more than one process.
    #
    # Prefix to rate, for the request-rate limit. The longest matching prefix
    # wins, so a specific path can carry a tighter limit than the blanket
    # prefix around it — the reset-token endpoint sends mail and is the one
    # worth throttling hardest.
    rate_limit_enabled: bool = True
    rate_limit_storage_uri: str = "async+memory://"
    rate_limit_rules: dict[str, str] = {
        "/api/v1/conversations": "20/minute",
        "/api/auth": "20/minute",
        "/api/auth/user/password/reset": "3/minute",
    }
    rate_limit_fail_open: bool = True

    # Durable per-user token quota (ADR-0024), layered under the provider's
    # spend cap and separate from the request-rate limit above.
    token_quota_enabled: bool = True
    token_quota_tokens: int = 100_000
    token_quota_period: str = "month"

    @property
    def supertokens_api_key_or_none(self) -> str | None:
        return self.supertokens_api_key or None


@lru_cache
def get_settings() -> Settings:
    return Settings()
