set dotenv-load := false

default:
    @just --list

COMPOSE := "docker compose -f infrastructure/docker/compose.yaml"
HOST_DEPS := "infrastructure/docker/compose.host-deps.yaml"

# Datastores only, plus migrations. CI and e2e use this and run the API and SPA
# on the host, so nothing else would apply them — and an unmigrated database
# looks like an API bug rather than a missing step.
dependencies:
    {{COMPOSE}} -f {{HOST_DEPS}} up -d --wait
    cd back-end && uv run alembic upgrade head

dependencies-stop:
    {{COMPOSE}} stop

# The whole stack behind Caddy at http://localhost (ADR-0026). Runs in the
# foreground; use development-logs in another terminal to follow output.
development:
    {{COMPOSE}} --profile full up --build

development-stop:
    {{COMPOSE}} --profile full stop

development-logs:
    {{COMPOSE}} --profile full logs -f

# `api` already waits on the compose `migrate` service, so this is only needed
# to apply a new revision to a stack that is already running.
development-migrate:
    {{COMPOSE}} --profile full run --rm migrate

back-end:
    cd back-end && uv run uvicorn ai_chat.main:app --reload --port 8000 --proxy-headers --forwarded-allow-ips "*"

front-end:
    cd front-end && pnpm dev --port 5173

test-back-end:
    cd back-end && uv run pytest

test-front-end:
    cd front-end && pnpm test

test-e2e:
    cd e2e && pnpm test

lint:
    cd back-end && uv run ruff check . && uv run ruff format --check .
    cd front-end && pnpm eslint . && pnpm prettier --check .

install:
    cd back-end && uv sync
    pnpm install
