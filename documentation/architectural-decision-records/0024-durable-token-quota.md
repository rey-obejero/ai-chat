# ADR-0024: The token quota is a Postgres ledger with a calendar period

- **Status:** Accepted
- **Date:** 2026-09-22
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Per-user token spend is a Postgres ledger, summed over the current period by a
route dependency that blocks a user who has exhausted their budget.

## Context

ADR-0019 ships one server-held provider key behind a global USD spend cap, and
ADR-0020 adds a per-user request-rate limit. But a rate limit bounds how *often*
a user may call, not how *much* each call costs: a handful of enormous prompts
can drain a shared budget without ever tripping a per-minute counter. The MVP
needs per-user budget control before it is exposed publicly.

Three forces shaped the choice. Spend must be attributable per user, so it has
to be durable and keyed by identity rather than process-local. Enforcement must
reject *before* an expensive call starts, and the rejection should use the
normal error envelope. And the accounting should be inspectable after the fact —
a running total alone cannot answer "what did this conversation cost".

## Decision

- Record one row per completed reply in a `token_usage` ledger (`user_id`,
  `conversation_id`, token counts, `created_at`), indexed on
  `(user_id, created_at)`.
- Take usage from the provider's terminal stream chunk rather than estimating
  it. OpenRouter sends it by default; the port carries it as `ChatChunk.usage`.
- Sum the current period on demand, where the period is calendar-aligned
  (`token_quota_period`, `month` by default) so the reset is predictable.
- Enforce with a route dependency on the reply endpoint, not middleware: it runs
  after authentication, and its `QuotaExceededError` reaches the registered
  problem+json handlers (ADR-0003). Rejections return `429` with code
  `QUOTA_EXCEEDED` and the seconds until the period resets.
- Check before the request rather than reserving per request: a user can exceed
  the budget by at most one reply, and the provider-side cap stays the hard
  backstop (ADR-0019).
- Keep the quota disabled in the shared test app and enable it only where it is
  under test, mirroring `rate_limit_enabled`.

## Consequences

- **Easier:** per-user fairness; a budget that survives restarts and applies
  across processes; an audit trail that supports a per-conversation cost view
  later; a rejection that reuses the normal error envelope.
- **Harder:** every reply pays a small indexed sum on the hot path, and the
  ledger grows with usage, so it will eventually need pruning or a rollup.
- **We now live with:** accounting is best-effort — a failure to record usage is
  logged and does not fail an otherwise successful reply, so an unavailable
  database could under-count spend while chat keeps working.

## Alternatives considered

- **Estimate tokens locally (tiktoken)** — no provider dependency, but
  approximate, model-specific, and drifts from what is actually billed.
- **A running counter row per user** — cheap reads, but needs its own reset and
  loses the per-request audit trail; a sum over an indexed ledger is fast enough
  at this scale.
- **Enforce in middleware, beside the rate limit** — one gate for every
  expensive route, but middleware cannot reuse the exception handlers and would
  have to hand-build the error body (ADR-0020 already pays that cost once).
- **Redis counters** — the rate limiter's store, but tokens are money and the
  ledger should be durable, not a cache that can be evicted.
- **Provider-side per-user limits (OpenRouter Management API)** — enforces at
  the vendor, but couples every account to OpenRouter and is more integration
  than this stage needs (ADR-0019).
