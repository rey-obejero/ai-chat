# AGENTS.md — back-end

FastAPI service for AI Chat. Root guide: `../AGENTS.md`.

## Stack (detailed)

- **Framework:** FastAPI (ASGI), uvicorn
- **Auth:** SuperTokens Python SDK (self-hosted; email/password + Google/GitHub)
- **ORM:** SQLAlchemy 2.x **async** (`asyncpg`), `AsyncSession`
- **Migrations:** Alembic (async `env.py`)
- **Config:** pydantic-settings (`Settings` read at startup, `.env` gitignored)
- **Validation:** Pydantic v2 at the boundary; domain rules in the service layer
- **Errors:** domain exceptions → one handler set → RFC 9457 problem+json
- **Tests:** pytest + pytest-asyncio (auto) + httpx `ASGITransport` + respx +
  Testcontainers (Postgres); ruff for lint/format
- **Package/env:** uv

## Layout

```
back-end/
├── src/ai_chat/
│   ├── main.py            # create_app(); owns the /api/v1 prefix; wires middleware
│   ├── shared/            # horizontal infra: config, db, exceptions, pagination,
│   │                      #   rate_limit (ASGI middleware, ADR-0020),
│   │                      #   streaming (AI SDK wire encoders, ADR-0012)
│   ├── auth/              # feature slice (models, schemas, service, router, port);
│   │                      #   identity.resolve_user_id serves middleware
│   ├── conversations/     # feature slice (models, schemas, service, router,
│   │                      #   streaming) — conversations + messages
│   ├── llm/               # feature slice (port, schemas, service, adapters/) — ADR-0018
│   ├── usage/             # feature slice (models, schemas, service, router) —
│   │                      #   token accounting + quota, ADR-0024
│   └── documents/         # future slice
├── tests/<feature>/{unit,integration}/
└── alembic/versions/      # migrations
```

## Commands

```sh
uv sync
uv run uvicorn ai_chat.main:app --reload --port 8000
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

From the repo root, prefer `just back-end` / `just test-back-end` / `just lint`.

## Architecture rules

- Business logic is **always vertical** in `src/ai_chat/<feature>/`.
  Cross-cutting infrastructure lives **only** in `shared/`.
- Every feature exposes a public API via its `__init__.py`; never import a
  feature's internals across boundaries.
- No mapper layer: `from_attributes=True` + `model_validate()` /
  `model_dump()`. SQLAlchemy models act as the domain layer.
- `main.py` owns the `/api/v1` router prefix. SuperTokens routes live under
  `/api/auth`.

## Error handling

- Service layer raises domain exceptions (subclasses of `AppError`). It never
  imports `fastapi` and never raises `HTTPException`.
- Registered handlers convert to RFC 9457 `application/problem+json`:
  `type` (`about:blank`), `title`, `status`, `detail`, `instance`, plus the
  `code` extension. Validation errors add an `errors` extension.
- The upgrade to per-class dereferenceable `type` URIs is tracked in
  `../documentation/roadmap.md`.

## Do

- Use `async def` for all I/O; inject `AsyncSession` via `Depends`.
- Keep request/response shapes in Pydantic schemas; keep DB models separate.
- Write migrations that are reversible and clearly named.
- Add tests by kind: pure logic in `unit/`, app/DB wiring in `integration/`.

## Don't

- Don't import `fastapi` (or `HTTPException`) inside service modules.
- Don't run blocking/sync DB calls inside async routes.
- Don't use `Result`/Either objects — Python uses exceptions (EAFP).
- Don't put domain rules in `shared/`.
- Don't leak exception internals in 500 responses (log server-side instead).
