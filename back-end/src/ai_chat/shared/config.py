import json
from functools import lru_cache
from typing import Annotated, Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# What `LLM_MODELS` accepts, stated once so the rejection message names both forms.
_LLM_MODELS_FORM = "LLM_MODELS must be a comma-separated list of ids or a JSON array of ids"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Chat"
    # Both are the browser origin, which is what makes the session cookie
    # same-site. The native lane serves the SPA on the Vite port and proxies
    # /api to the API, so the API's own port is not the origin (ADR-0046).
    api_base_url: str = "http://localhost:5173"
    frontend_url: str = "http://localhost:5173"

    database_url: str = "postgresql+asyncpg://aichat:aichat@localhost:5433/aichat"

    supertokens_connection_uri: str = "http://localhost:3567"
    supertokens_api_key: str = ""

    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""

    # Password screening (ADR-0038, FR-2). Length is checked locally; `zxcvbn`
    # scores entropy 0–4 and rejects below `password_min_score`; the breach check
    # asks the HIBP range API for the password's hash prefix. The breach check
    # is on by default and fails *open* when the service is unreachable, so a
    # blocked sign-up is always the password's fault, never the network's.
    password_min_score: int = 2
    password_breach_check_enabled: bool = True
    hibp_api_key: str = ""
    hibp_timeout_seconds: float = 2.0

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
    # What the model picker offers (FR-23). Empty means "just `llm_model`",
    # which is also what a single-model deployment gets without setting
    # anything: multi-model support is an environment change, not a code one.
    # Written either as a comma-separated list or as a JSON array; `NoDecode`
    # is what lets the comma form arrive (see `_parse_llm_models`).
    llm_models: Annotated[list[str], NoDecode] = []
    llm_embedding_model: str = "openai/text-embedding-3-small"
    llm_max_output_tokens: int = 1024
    llm_request_timeout: float = 60.0

    # Rate limiting (ADR-0020). Memory storage in development; switch to
    # "async+redis://…" once the API runs more than one process.
    #
    # Prefix to rate, for the request-rate limit. The longest matching prefix
    # wins, so a specific path can carry a tighter limit than the blanket
    # prefix around it — the endpoints that send mail are the ones worth
    # throttling hardest, because each allowed call costs a message. The
    # verification resend is the tighter rule for the same reason as the reset
    # token: without it, resends ride the 20/minute auth prefix and an account
    # can be made to send twenty mails a minute.
    rate_limit_enabled: bool = True
    rate_limit_storage_uri: str = "async+memory://"
    rate_limit_rules: dict[str, str] = {
        "/api/v1/conversations": "20/minute",
        "/api/v1/media": "60/minute",
        "/api/auth": "20/minute",
        "/api/auth/user/password/reset": "3/minute",
        "/api/auth/user/email/verify/token": "3/minute",
    }
    rate_limit_fail_open: bool = True

    # How long a conversation may stay claimed by an in-flight stream before a
    # later writer is allowed to take it over (ADR-0052). A crashed worker
    # self-heals instead of wedging the conversation forever.
    stream_grace_seconds: int = 120

    # Durable per-user token quota (ADR-0024), layered under the provider's
    # spend cap and separate from the request-rate limit above. An unverified
    # account gets the reduced allowance (ADR-0039); unset means half of
    # `token_quota_tokens`, so a deployment that changes the quota changes both
    # and the reduction cannot be lost by forgetting the second value.
    token_quota_enabled: bool = True
    token_quota_tokens: int = 100_000
    token_quota_unverified_tokens: int | None = None
    token_quota_period: str = "month"

    # Server-side image proxy (ADR-0051). Disabling it removes the route
    # entirely, so a deployment can opt out without an open endpoint lingering.
    media_proxy_enabled: bool = True
    media_max_bytes: int = 5_242_880
    media_timeout_seconds: float = 10.0
    media_max_redirects: int = 4
    media_cache_ttl_seconds: int = 86_400

    @property
    def supertokens_api_key_or_none(self) -> str | None:
        return self.supertokens_api_key or None

    @field_validator("llm_models", mode="before")
    @classmethod
    def _parse_llm_models(cls, value: object) -> object:
        """Read the list from either form an operator can reasonably write.

        The `NoDecode` annotation on the field is what makes a hand-written
        value reach this at all: without it the environment source JSON-decodes
        a complex field before validation, so `a,b` fails there and the process
        never starts.
        """
        if not isinstance(value, str):
            return value

        text = value.strip()
        if text.startswith(("[", "{")):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as error:
                raise ValueError(_LLM_MODELS_FORM) from error
            if not isinstance(parsed, list):
                raise ValueError(_LLM_MODELS_FORM)
            return parsed
        return [item.strip() for item in text.split(",") if item.strip()]

    @model_validator(mode="after")
    def _resolve_llm_models(self) -> Self:
        """Make `llm_model` invariably one of the served models (FR-23).

        It is the default a request without a choice goes to, so it has to be
        in the list the picker offers: otherwise the list would have no
        `is_default` entry, and nothing to fall back to. Duplicates collapse,
        because the picker would otherwise show one model twice.
        """
        models = [model for model in dict.fromkeys(self.llm_models) if model]
        if self.llm_model not in models:
            models.insert(0, self.llm_model)
        self.llm_models = models
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
