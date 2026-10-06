# Roadmap

Living build tracker for `ai-chat`. Requirements live in
[`functional-requirements.md`](functional-requirements.md).

Architectural decisions are recorded as ADRs in
[`architectural-decision-records/`](architectural-decision-records/README.md);
this file tracks build progress, not decision rationale.

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

## Known front-end defects

Recorded rather than fixed; each is visible on inspection and can be picked up
when it next draws attention.

- **Group-header chevrons never appear.** `SidebarGroup.vue` reveals the chevron
  with `group-hover:opacity-100`, and that variant is inert in this build — the
  button is genuinely `:hover` while the chevron stays at `opacity: 0`. Any
  reliance on a `group-*` variant should be treated as broken until verified in
  a browser. The fix is a scoped `:hover` / `:focus-within` rule, which is what
  the collapsed-sidebar logo toggle now uses.
- **PrimeVue's unlayered stylesheet outranks Tailwind utilities.** Unlayered CSS
  beats `@layer utilities` regardless of specificity, so a utility on a PrimeVue
  component needs `!` to land. This is why the icon buttons carry
  `!size-8 !p-0`, the collapsed toggle needs `!absolute`, and the model selector
  needs `!text-body-sm` — without it, PrimeVue's 16px button font-size wins and
  the control renders larger than its peers.

## Next: a public deploy

The capped OpenRouter key, a single-VPS Compose stack behind Caddy with
automatic TLS, and the deploy runbook.

## Deferred: containerized stack

SeaweedFS (document storage) stays out of the compose files under
`infrastructure/docker/` until the documents slice lands. The self-hosted
compose file is the production-shaped stack (ADR-0046); add SeaweedFS there when
the feature does.

## Error envelope — future upgrade

- [ ] RFC 9457 `type` URIs. Currently `type: "about:blank"` + a `code`
      extension member identifies the problem class. Upgrade: give each error
      class its own dereferenceable documentation URI (e.g.
      `https://<host>/problems/not-authenticated`) and a meaningful `title`,
      keeping `code`. Non-breaking/additive.
