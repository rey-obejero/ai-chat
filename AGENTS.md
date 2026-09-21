# AGENTS.md — AI Chat

A ChatGPT-style chat bot with document retrieval (RAG), tool calling, and custom
skills. Chat first — retrieval and tools are capabilities the assistant uses,
not the product.

Sources of truth:
- Stack + features: `~/documents/ai-chat-assistant.md`
- Build tracker / debt: `documentation/roadmap.md`
- UI design system: `DESIGN.md` (binding on all front-end work)

## Monorepo layout

```
ai-chat/
├── back-end/     FastAPI service (uv, Python)
├── front-end/    Vue 3 + Vite SPA (pnpm)
├── e2e/          Playwright end-to-end tests (pnpm workspace package)
├── documentation/  roadmap + design notes
├── Caddyfile     reverse proxy (same-origin /api → API, /* → SPA)
├── compose.yaml  local dev dependencies (postgres+pgvector, supertokens)
└── Justfile      task runner
```

## Stack (locked)

| Layer | Choice |
|---|---|
| Back-end | Python — FastAPI |
| Front-end | Vue 3 + Vite SPA (not Nuxt) |
| UI | PrimeVue 4 + Tailwind CSS v4 |
| Auth | SuperTokens (self-hosted; email/password + Google/GitHub) |
| Database | PostgreSQL for everything (pgvector + `tsvector`) |
| ORM | SQLAlchemy 2.x (async) |
| Tooling | uv (Python) · pnpm (JS) · just · Docker Compose · Caddy |
| Hooks | Husky + commitlint + lint-staged |
| Errors | RFC 9457 `application/problem+json` |

## Architecture rules

- Feature-sliced (option B + D): business logic is **always** vertical
  (`back-end/src/ai_chat/<feature>/`, `front-end/src/features/<feature>/`).
  Cross-cutting infrastructure is horizontal only in `shared/` (back-end).
- Every feature exposes an explicit public API (`__init__.py` / `index.ts`);
  never import a feature's internals across boundaries.
- Tests (T3): mirror the slice, then split by kind —
  `back-end/tests/<feature>/{unit,integration}/`.
- `main.py` owns the `/api/v1` router prefix.

## Execution commands

Prerequisites: `uv`, `pnpm` 10.15.0, `docker`, `just`.

```sh
just install        # uv sync + pnpm install
just dependencies   # postgres + supertokens (docker compose up)
just dependencies-stop
just back-end       # FastAPI on :8000 (reload)
just front-end      # Vite dev server on :5173
just test-back-end  # back-end pytest
just test-front-end # front-end vitest
just test-e2e       # Playwright (root e2e/)
just lint           # ruff + eslint + prettier
```

`just test-e2e` starts its own SPA, API, and mock model provider. Stop any
running dev servers first, or Playwright will reuse them and the chat specs will
fail to reach the mock (ADR-0023).

Dev runs the API and SPA directly (`:8000` / `:5173`); Vite proxies `/api`.
Running the whole stack in containers (api + Caddy) is deferred.

## Conventions

- Conventional Commits (enforced by commitlint). Branches: `feature/`, `fix/`,
  `refactor/`.
- **Never commit unless a human explicitly approves it.**

## Sub-guides

- `back-end/AGENTS.md` — Python/FastAPI specifics
- `front-end/AGENTS.md` — Vue/TS specifics and the design system
- `DESIGN.md` — UI contract (colors, typography, spacing)
