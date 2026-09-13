# Roadmap

Living build tracker for `ai-chat`. Source of truth for stack and features:
`~/documents/ai-chat-assistant.md`.

## Tooling debt

- [x] Removed gitleaks from pre-commit hook (was failing with 127, binary
      not installed). CI `gitleaks` job still scans on push/PR.
- [x] Installed `just` (1.57.0) and `uv` (`~/.local/bin`).

## Done: auth happy path

Email/password + Google/GitHub social login (SuperTokens), async SQLAlchemy,
app-level `users` + `conversations` tables (Alembic revision `0001`), guarded
`/me`, and a protected chat shell. All errors use RFC 9457 problem+json,
including SuperTokens' own 401s. Front-end ships custom PrimeVue 4 forms
styled through the DESIGN.md Tailwind v4 tokens.

## Next: streaming chat

Pinned SSE protocol (AI SDK v1) with a hand-rolled FastAPI emitter, message
persistence, and the conversation/message list UI.

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
