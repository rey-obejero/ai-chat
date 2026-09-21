# ADR-0020: Rate limiting is Redis-backed ASGI middleware

- **Status:** Accepted
- **Date:** 2026-09-22
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

A pure-ASGI middleware limits requests per user with a sliding-window counter in
Redis, scoped to expensive routes and failing open.

## Context

The application is public with open signups and runs on a shared provider key
(ADR-0019), so abuse directly costs money. Chat requests are unusually expensive
and slow — a streaming reply can hold a connection for a minute — and their cost
varies enormously between a one-line prompt and a large retrieval-augmented one.
Rate limiting is therefore both a service-protection and a cost-control concern.

A second question was placement: a global middleware choke point versus a
per-route dependency. A dependency runs after authentication, which makes the
current user available for free and lets rejections use the normal error
handlers. Middleware runs before routing and before dependencies, so it must
resolve identity itself, but it guarantees that no expensive route can be added
without a limit. The middleware placement was chosen deliberately.

## Decision

- Implement the limiter in `shared/rate_limit/` — cross-cutting infrastructure
  belongs in `shared/` (ADR-0001).
- Use pure ASGI middleware, never `BaseHTTPMiddleware`, so streaming responses
  are never buffered or wrapped (ADR-0012).
- Use the `limits` library's async storage and strategies, with a
  sliding-window counter. Fixed windows were rejected because their boundary
  burst permits up to twice the limit in a short span, which is costly when each
  request is a paid completion.
- Storage is taken from `Settings.rate_limit_storage_uri`: `async+memory://`
  locally, `async+redis://…` when the API runs more than one process. The
  strategy object is identical either way.
- Requests are keyed by `user:{id}`, falling back to `ip:{client.host}` for
  unauthenticated callers.
- Identity is resolved by an injected callable from `auth` (wrapping the
  provider's session verification), so `shared/rate_limit` never imports a
  feature. The route dependency verifies independently; SuperTokens validates
  the access token locally, so a second check is cheap.
- The middleware is path-scoped to the expensive routes (`/api/v1/conversations`
  and future message/streaming endpoints). Auth and health endpoints are
  excluded.
- Rejections return `application/problem+json` with `status: 429` and
  `Retry-After`, built by the middleware itself, because responses produced in
  middleware never reach the registered exception handlers (ADR-0003).
- If the limiter's storage is unreachable, the middleware fails open. The
  provider-side spend cap is the hard backstop, so availability wins.
- A durable per-user token quota in Postgres is a separate, complementary tier
  that defends the budget; a request-rate limit alone cannot stop a few
  enormous prompts. A per-user concurrency cap is likewise considered separately
  from the per-minute rate.

## Consequences

- **Easier:** one global gate that covers every expensive route by
  construction; per-user fairness; Redis only becomes necessary when the API
  scales beyond one process.
- **Harder:** identity must be resolved before it would otherwise be needed, and
  the session is verified twice (a local JWT check, so cheap); the 429 body
  cannot reuse the exception handlers; the IP fallback requires proxy-header
  handling or every request behind the reverse proxy collapses into one bucket.
- **We now live with:** a Redis dependency in any multi-process deployment, a
  middleware whose correctness matters to cost control, and the rule that a
  request-rate limit is not a budget control — the quota is.

## Alternatives considered

- **A per-route dependency** — cleaner identity and error handling, but opt-in,
  so a new expensive route can silently ship unlimited; rejected for that
  reason.
- **`slowapi`'s default fixed window** — simplest, but the boundary burst is a
  real cost spike here.
- **Moving window (sliding log)** — exact, but state grows with the limit.
- **Postgres-backed counters** — no new service and shares the quota store, but
  puts writes on the hot path and needs cleanup.
- **Edge limiting in Caddy** — per-IP only, with no user identity.
- **Provider-side limits alone** — global, not per-user, so one account can
  exhaust everyone's budget.
