# AI Chat

## Stack

| Layer     | Choice                                    |
| --------- | ----------------------------------------- |
| Back-end  | Python — FastAPI                          |
| Front-end | Vue 3 + Vite SPA                          |
| UI        | PrimeVue 4 + Tailwind CSS v4              |
| Auth      | SuperTokens (self-hosted)                 |
| Database  | PostgreSQL (pgvector + `tsvector`)        |
| ORM       | SQLAlchemy 2.x (async)                    |
| Tooling   | uv · pnpm · just · Docker Compose · Caddy |

## Layout

```
ai-chat/
├── back-end/   FastAPI service
├── front-end/  Vue 3 SPA
├── e2e/        Playwright tests
└── documentation/
```

## Quickstart

Prerequisites: `uv`, `pnpm` 10.15.0, `docker`, `just`.

```sh
just install        # install back-end + front-end dependencies
just dependencies   # start postgres + supertokens
just dependencies-stop
just back-end       # FastAPI on :8000
just front-end      # Vite on :5173
just test-back-end  # back-end tests
just test-front-end # front-end tests
just test-e2e       # end-to-end tests
just lint           # lint + format checks
```

## Docs

- `AGENTS.md` — stack, commands, architecture rules
- `back-end/AGENTS.md`, `front-end/AGENTS.md` — per-package guides
- `DESIGN.md` — UI design system
- `documentation/roadmap.md` — build tracker
