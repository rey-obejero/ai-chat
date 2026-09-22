# Roadmap

Living build tracker for `ai-chat`. Source of truth for stack and features:
`~/documents/ai-chat-assistant.md`.

Architectural decisions are recorded as ADRs in [`adrs/`](adrs/README.md); this
file tracks build progress, not decision rationale.

## Tooling debt

- [x] Removed gitleaks from pre-commit hook (was failing with 127, binary
      not installed). CI `gitleaks` job still scans on push/PR.
- [x] Installed `just` (1.57.0) and `uv` (`~/.local/bin`).

## Done: auth happy path

Email/password + Google/GitHub social login (SuperTokens), async SQLAlchemy,
app-level `users` + `conversations` tables (Alembic revision `0001`), guarded
`/me`, and a protected conversations view. All errors use RFC 9457 problem+json,
including SuperTokens' own 401s. Front-end ships custom PrimeVue 4 forms
styled through the DESIGN.md Tailwind v4 tokens.

## Done: streaming replies (back-end)

`POST /conversations/{id}/messages` streams the assistant reply as SSE in the AI
SDK UI Message Stream v1 format and persists both turns; a `messages` table and
migration (`0002`) back it (ADR-0012, ADR-0022).

## Done: the conversation view

Message list, streaming rendering, and the composer wired to the endpoint via
`@ai-sdk/vue` with a custom transport, covered end to end against a deterministic
mock provider (ADR-0022, ADR-0023).

## Done: the token quota

Per-user token spend is a Postgres ledger summed over a calendar period, with a
route dependency that blocks a user who has exhausted their budget and a
settings modal that reports the remaining allowance (ADR-0024).

## Next: a public deploy

The capped OpenRouter key, a single-VPS Compose stack behind Caddy with
automatic TLS, and the deploy runbook.

## Deferred: containerized stack

Removed from `compose.yaml` until their features land: SeaweedFS (document
storage), the `api` container, and Caddy. `compose.yaml` now carries only the
local dev dependencies (postgres + supertokens). Reintroduce each when needed.

## Error envelope — future upgrade

- [ ] RFC 9457 `type` URIs. Currently `type: "about:blank"` + a `code`
      extension member identifies the problem class. Upgrade: give each error
      class its own dereferenceable documentation URI (e.g.
      `https://<host>/problems/not-authenticated`) and a meaningful `title`,
      keeping `code`. Non-breaking/additive.
