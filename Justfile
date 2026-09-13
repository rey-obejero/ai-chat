set dotenv-load := false

default:
    @just --list

dependencies:
    docker compose up

dependencies-stop:
    docker compose stop

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
