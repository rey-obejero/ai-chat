# ADR-0011: Sessions use httpOnly, same-origin cookies

- **Status:** Accepted
- **Date:** 2026-09-22
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Session state lives in httpOnly cookies on a single origin; no token is ever
stored in web storage.

## Context

Storing a session or identity token in `localStorage` exposes it to any
JavaScript that runs on the page, so a single XSS becomes full account takeover.
The app also needs the SPA and API to cooperate without a separate backend
proxy layer.

## Decision

- SuperTokens' session recipe: httpOnly cookie, anti-CSRF token, and silent
  refresh, validated server-side.
- No identification or claims token in `localStorage` or `sessionStorage`.
- Same-origin deployment: Caddy path-routes `/api` to FastAPI and serves the SPA
  statically, so there is no CORS-for-credentials setup.
- No BFF layer: FastAPI is the only trust boundary and the only holder of
  secrets; the SPA never touches Postgres, SuperTokens, object storage, or the
  LLM provider directly.
- Routes that must be public are excluded at the router level, not at the proxy.

## Consequences

- **Easier:** XSS cannot read the session; no CORS credential configuration to
  get wrong; the SPA holds only UI state.
- **Harder:** local development relies on the Vite proxy to keep requests
  same-origin; a future cross-origin client would need a deliberate design.
- **We now live with:** the client can never read the session token — auth state
  comes from an endpoint, not from cookie inspection.

## Alternatives considered

- **Bearer tokens in `localStorage`** — rejected outright.
- **A BFF layer** — an extra hop and process for no benefit at this scale.
- **Cross-origin API with credentialed CORS** — more moving parts and a wider
  CSRF surface.
