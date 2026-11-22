# ADR-0032: Rate limiting runs outside SuperTokens and covers the auth endpoints

- **Status:** Accepted
- **Date:** 2026-10-04
- **Deciders:** Rey Obejero
- **Supersedes:** ADR-0020
- **Superseded by:** —

## TL;DR

The rate limiter keeps its Redis-backed sliding-window design, but it now runs
ahead of the SuperTokens middleware and covers the authentication endpoints,
with a per-prefix rate so the reset endpoint that sends mail is throttled
harder than sign-in.

## Context

ADR-0020 chose a pure-ASGI middleware, keyed per identity, scoped to the
expensive routes and failing open. Two things then proved wrong with the
scoping and placement, and both were invisible until real traffic arrived.

**Placement.** The limiter was added *before* the SuperTokens middleware. In
Starlette the last-added middleware is outermost, so SuperTokens stayed
outermost — and because it answers `/api/auth/*` itself without calling the
wrapped app, the limiter never ran for an auth request at all.

**Scope.** Auth endpoints were excluded on the assumption that they were cheap.
They are not only cheap to attack: sign-in accepts unlimited password guesses
per source, and the reset-token endpoint sends mail, so an unthrottled one is an
email cannon aimed at an arbitrary third-party address. Forgot password made
that exposure concrete.

The original ADR's scoping decision was therefore wrong on both counts, which is
why this record supersedes it rather than a bug being fixed quietly.

## Decision

- Implement the limiter in `shared/rate_limit/` (ADR-0001) as **pure ASGI
  middleware**, never `BaseHTTPMiddleware`, so streams are not buffered
  (ADR-0012).
- Use the `limits` library's async storage and **sliding-window counter**, from
  `Settings.rate_limit_storage_uri` — `async+memory://` locally,
  `async+redis://…` once more than one process serves requests.
- Key requests by `user:{id}`, falling back to `ip:{client.host}` for
  unauthenticated callers. Auth calls are unauthenticated, so they key on the
  source address, which is correct: both attacks are per-source.
- Resolve identity through an injected callable from `auth`, so
  `shared/rate_limit` never imports a feature.
- **Placement is the correction:** the limiter is added *after* the SuperTokens
  middleware, so it is outermost and runs first. Any future middleware must
  preserve this order, or auth limits silently stop applying.
- **Scope is the correction:** the defaults cover `/api/v1/conversations`,
  `/api/auth`, and a tighter `/api/auth/user/password/reset`.
- **Rate is per prefix, not global.** Rules are a prefix-to-rate map and the
  longest matching prefix wins, so a single endpoint can be throttled harder
  than the prefix that otherwise covers it without a second middleware. Each
  rule counts in its own namespace.
- Rejections return `application/problem+json` with `status: 429` and
  `Retry-After`, built by the middleware itself, because middleware responses
  never reach the registered exception handlers (ADR-0003).
- If the storage is unreachable the limiter **fails open**; the provider-side
  spend cap and the token quota are the hard backstops.

## Consequences

- **Easier:** one gate covers chat and credential endpoints by construction;
  per-endpoint tightening is a config edit; the same storage serves every rule.
- **Harder:** middleware order is now load-bearing and a reordering breaks auth
  limits silently; the IP fallback requires proxy-header handling or every
  request behind the reverse proxy collapses into one bucket.
- **We now live with:** a Redis dependency in any multi-process deployment, and
  the rule that a request-rate limit is not a budget control — the durable token
  quota (ADR-0024) is.

## Alternatives considered

- **Keep the limiter under SuperTokens and accept that auth is unlimited** —
  rejected; it is the gap this record exists to close.
- **A single prefix with one rate for all auth endpoints** — rejected as too
  blunt. Sign-in and the mail-sending reset endpoint have different abuse costs,
  so they carry different limits.
- **A per-route dependency instead of middleware** — cleaner identity and error
  handling, but opt-in, so a new expensive route can silently ship unlimited.
- **`slowapi`'s fixed window** — simplest, but the boundary burst is a real cost
  spike when each request can be a paid completion.
- **Postgres-backed counters** — no new service, but writes on the hot path.
- **Edge limiting in Caddy** — per-IP only, with no user identity.
