# ADR-0016: Caddy is the single origin

- **Status:** Accepted
- **Date:** 2026-09-22
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

One Caddy reverse proxy serves the SPA and routes `/api` to FastAPI, giving the
application a single origin with automatic TLS.

## Context

The session model depends on httpOnly, same-origin cookies (ADR-0011). Serving
the SPA and the API from different origins would require credentialed CORS and a
carefully configured cookie policy, and the deployment still needs TLS and
static file serving.

## Decision

- Caddy terminates TLS and reverse-proxies.
- Path routing: `/api/*` to the FastAPI service, everything else to the static
  SPA build.
- No CORS-for-credentials configuration exists because there is no cross-origin
  request.
- In development, Vite's proxy plays the same role with the SPA and API on
  separate ports.

## Consequences

- **Easier:** cookies and CSRF are straightforward; TLS is automatic; one place
  defines the public routing surface.
- **Harder:** production routing differs from dev routing, so proxy behavior
  must be exercised separately; the proxy config is a deployment artifact that
  can drift from the app.
- **We now live with:** the rule that anything the browser calls must be
  reachable through this one origin.

## Alternatives considered

- **Nginx** — reserved for a sibling project; Caddy's automatic TLS and simpler
  config were preferred here.
- **Traefik** — service-discovery features this deployment doesn't use.
- **Separate origins with CORS credentials** — more moving parts and a wider
  failure surface for no benefit.
