# Roadmap

Living build tracker for `ai-chat`. Source of truth for stack and features:
`~/documents/ai-chat-assistant.md`.

## Tooling debt

- [x] Removed gitleaks from pre-commit hook (was failing with 127, binary
      not installed). CI `gitleaks` job still scans on push/PR.
- [ ] Install `just` binary (Justfile unrunnable until then).

## Next: auth happy path

Email/password + Google/GitHub social login (SuperTokens), async SQLAlchemy,
custom PrimeVue forms, app-level `users` + `conversations` tables with Alembic
migration. Guarded `/me` route + protected chat shell via Caddy same-origin
httpOnly-cookie flow.
