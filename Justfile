set dotenv-load := false

default:
    @just --list

COMPOSE_DEV := "docker compose -f infrastructure/docker/compose.dev.yaml"
COMPOSE_SELFHOST := "docker compose -f infrastructure/docker/compose.selfhost.yaml"
E2E_COMPOSE := "docker compose -p ai-chat-e2e -f infrastructure/docker/compose.selfhost.yaml -f infrastructure/docker/compose.e2e.yaml"
DEV_DEPS := "postgres supertokens redis mailpit"

# Datastores only, plus migrations. Used by the native lane, and by CI and the
# e2e suite, which run the API and SPA on the host. The development file
# publishes the datastore ports, so a host-run API reaches them by `localhost`.
dependencies:
    {{COMPOSE_DEV}} up -d --wait {{DEV_DEPS}}
    cd back-end && uv run alembic upgrade head

dependencies-stop:
    {{COMPOSE_DEV}} stop {{DEV_DEPS}}

# Native development (the default): dependencies in Compose, the API and the SPA
# on the host. The browser origin is the Vite port; Vite proxies /api to the API
# on :8000, so the app is still single-origin without a reverse proxy
# (ADR-0046). Ctrl-C stops both host processes; the datastores keep running.
development: dependencies
    #!/usr/bin/env sh
    set -eu
    ( cd back-end && exec uv run uvicorn ai_chat.main:app --reload --port 8000 --proxy-headers --forwarded-allow-ips "*" ) &
    api=$!
    ( cd front-end && exec pnpm dev --port 5173 ) &
    spa=$!
    trap 'kill "$api" "$spa" 2>/dev/null || true' EXIT INT TERM
    wait

# Containerized development: the whole stack in Compose, no reverse proxy. The
# browser origin is the published Vite port.
development-containerized:
    {{COMPOSE_DEV}} up --build

development-stop:
    {{COMPOSE_DEV}} stop

development-logs:
    {{COMPOSE_DEV}} logs -f

# `api` already waits on the compose `migrate` service, so this is only needed
# to apply a new revision to a stack that is already running.
development-migrate:
    {{COMPOSE_DEV}} run --rm migrate

# Self-hosted production: the built SPA behind Caddy and the API from its image,
# on one origin. Caddy is the only published service. Set SITE_ADDRESS (and the
# application's own settings in `back-end/.env`) for a real deployment.
self-host:
    {{COMPOSE_SELFHOST}} up --build

self-host-stop:
    {{COMPOSE_SELFHOST}} stop

self-host-logs:
    {{COMPOSE_SELFHOST}} logs -f

back-end:
    cd back-end && uv run uvicorn ai_chat.main:app --reload --port 8000 --proxy-headers --forwarded-allow-ips "*"

front-end:
    cd front-end && pnpm dev --port 5173

test-back-end:
    cd back-end && uv run pytest

test-front-end:
    cd front-end && pnpm test

# Independent end-to-end run: build the self-hosted stack and a Playwright
# runner, run the suite in containers against the deterministic mock providers,
# then remove the whole project and its volumes. Needs only Docker, and cannot
# touch a running development stack (its own project, its own empty database).
test-e2e:
    #!/usr/bin/env sh
    set -eu
    export HTTP_PORT=18080 HTTPS_PORT=18443 SITE_ADDRESS=http://caddy
    mkdir -p e2e/test-results e2e/playwright-report
    compose="{{E2E_COMPOSE}}"
    $compose --profile test build
    $compose up -d --wait
    trap '$compose down -v --remove-orphans' EXIT
    $compose --profile test run --rm e2e

lint:
    cd back-end && uv run ruff check . && uv run ruff format --check .
    cd front-end && pnpm eslint . && pnpm prettier --check .

install:
    cd back-end && uv sync
    pnpm install
