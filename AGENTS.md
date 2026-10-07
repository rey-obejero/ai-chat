# AGENTS.md — AI Chat

A multi-user chat assistant with document retrieval (RAG), tool calling, and
custom skills. Chat first — retrieval and tools are capabilities the assistant
uses, not the product.

Sources of truth:
- Requirements: `documentation/functional-requirements.md`
- Stack decisions: `documentation/architectural-decision-records/`
- Work tracking: the issue tracker
- UI design system: `DESIGN.md` (binding on all front-end work)

## Pending

- **File the work items as GitHub issues.** The FRD's Appendix A lists WI-1 …
  WI-17; create them in the issue tracker and record the issue numbers back in
  that table.
- **Retire `documentation/roadmap.md`.** Migrate its remaining items (known
  defects, tooling debt, the deferred-stack note, and the error-envelope
  upgrade) to issues, then delete the file.

## Monorepo layout

```
ai-chat/
├── back-end/     FastAPI service (uv, Python)
├── front-end/    Vue 3 + Vite SPA (pnpm)
├── e2e/          Playwright end-to-end tests (pnpm workspace package)
├── documentation/  requirements, ADRs, and design notes
├── infrastructure/docker/  compose files and deployment artifacts
│   ├── Caddyfile              self-host front door (/api → API, /* → built SPA)
│   ├── compose.dev.yaml       containerized development (Vite, no proxy)
│   └── compose.selfhost.yaml  self-hosted production (built SPA behind Caddy)
├── Justfile      task runner
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
just install                    # uv sync + pnpm install
just development                # native: datastores in Compose, API + SPA on the host
just development-containerized  # the whole stack in Compose, no proxy
just development-stop
just development-logs
just development-migrate        # apply pending migrations to a running stack
just self-host                  # self-hosted production stack (Caddy, built SPA)
just self-host-stop
just dependencies               # datastores only (postgres, supertokens, redis, mailpit)
just dependencies-stop
just back-end                   # FastAPI on :8000 (reload) — for debugging
just front-end                  # Vite dev server on :5173
just test-back-end              # back-end pytest
just test-front-end             # front-end vitest
just test-e2e                   # containerized Playwright run (own stack, Docker only)
just lint                       # ruff + eslint + prettier
```

`just development` is the normal workflow: the datastores run in Compose and the
API and SPA run natively, so reload is instant. The browser origin is the Vite
port (`http://localhost:5173`), and Vite proxies `/api` to the API, so the app is
single-origin without a reverse proxy (ADR-0046). `just development-containerized`
runs the whole stack in Compose instead.

`just back-end` and `just front-end` remain for debugging.

**Do not run the end-to-end tests any other way.** `just test-e2e` builds and
starts the whole stack in its own Compose project, with its own empty database,
and removes it afterward, so it needs no running development server and cannot
touch development data. Never leave a development server running for it.

## Releasing

Releases are automated with [release-please](https://github.com/googleapis/release-please),
driven by the Conventional Commits commitlint already enforces.

- Pushing to `main` runs the `release-please` workflow, which keeps a **Release
  PR** open that bumps the version in the root `package.json` and updates
  `CHANGELOG.md`.
- Merge that PR when you want to release. Merging tags the commit (`vX.Y.Z`) and
  creates the GitHub Release. Nothing is deployed by it.
- To force a version, put `Release-As: x.y.z` in a commit body.
- While pre-1.0, `bump-minor-pre-major` keeps a breaking change as a minor bump.
- The workflow uses `secrets.RELEASE_PLEASE_TOKEN` when set, otherwise
  `GITHUB_TOKEN`. Without the PAT secret, the Release PR is opened but does not
  trigger other workflows.
- The `RELEASE_PLEASE_TOKEN` PAT **expires**; when it does, releases fail until
  it is replaced. The durable alternative is a GitHub App installation token
  (minted per run, no expiry) — revisit this if renewal becomes a chore.

## Conventions

- Conventional Commits (enforced by commitlint). Branches: `feature/`, `fix/`,
  `refactor/`.
- **Never commit unless a human explicitly approves it.**

## Sub-guides

- `back-end/AGENTS.md` — Python/FastAPI specifics
- `front-end/AGENTS.md` — Vue/TS specifics and the design system
- `DESIGN.md` — UI contract (colors, typography, spacing)
