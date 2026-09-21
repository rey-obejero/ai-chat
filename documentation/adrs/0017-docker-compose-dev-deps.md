# ADR-0017: Compose runs dev dependencies only

- **Status:** Accepted
- **Date:** 2026-09-22
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Docker Compose provides the stateful development dependencies (Postgres and
SuperTokens); the API and SPA run natively for fast reloads.

## Context

Postgres with pgvector and SuperTokens are stateful services that are painful to
install by hand and should match production closely. The application code,
however, benefits from instant reload and direct debugging, which containerized
dev servers slow down.

## Decision

- `compose.yaml` defines `postgres` (image `pgvector/pgvector:pg16`, with an
  init script) and `supertokens` (built on the Postgres image).
- `just dependencies` starts them; `just back-end` and `just front-end` run the
  application processes on `:8000` and `:5173`.
- The SPA's `/api` calls are proxied to the API by Vite in development.
- The `api` container, Caddy, and object storage are deferred and removed from
  compose until their features land.

## Consequences

- **Easier:** real Postgres and SuperTokens locally with one command; hot reload
  and debuggers work normally.
- **Harder:** host ports must be managed and can collide; the native process
  environment differs from the eventual container image.
- **We now live with:** a compose file that is intentionally incomplete, to be
  extended as deployment features arrive.

## Alternatives considered

- **Containerize everything, including dev servers** — slower feedback loop.
- **No compose, manual installs** — inconsistent environments and setup
  friction.
- **A cloud dev database** — network dependency and shared state.
