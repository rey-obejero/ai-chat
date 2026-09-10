# AI Chat Assistant — task runner (requires https://just.systems)
set dotenv-load := false

default:
    @just --list

# ---- dev ----
dev-api:
    cd back-end && uv run uvicorn ai_chat_assistant.main:app --reload --port 8000

dev-web:
    cd front-end && pnpm dev --port 5173

# ---- compose ----
up:
    docker compose up --build

up-d:
    docker compose up --build -d

down:
    docker compose down

logs:
    docker compose logs -f

# ---- test / lint ----
test-api:
    cd back-end && uv run pytest

test-web:
    cd front-end && pnpm test

lint:
    cd back-end && uv run ruff check . && uv run ruff format --check .
    cd front-end && pnpm eslint . && pnpm prettier --check .

hooks-install:
    pnpm install && npx husky
