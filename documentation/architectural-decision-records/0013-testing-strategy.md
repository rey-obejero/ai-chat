# ADR-0013: Testing strategy

- **Status:** Accepted
- **Date:** 2026-09-22
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Fast unit tests plus real-infrastructure integration tests on the back-end,
component tests on the front-end, and Playwright for end-to-end flows.

## Context

Tests need to be fast enough to run on every save and honest enough to catch
integration failures. The database behavior (extensions, constraints, vector
operations) is exactly where mocks lie, while the LLM provider is an external
HTTP dependency we neither want to call nor fully mock away.

## Decision

- Back-end: `pytest` with `pytest-asyncio` in auto mode, `httpx` with
  `ASGITransport` for in-memory app tests, `respx` to fake provider HTTP calls,
  and Testcontainers for a real throwaway Postgres in integration tests.
- Tests mirror the slice and are split by kind: `tests/<feature>/{unit,integration}/`.
- Front-end: Vitest with Vue Test Utils (not `@testing-library/vue`) plus MSW
  for network faking.
- End-to-end: Playwright in the root `e2e/` package.
- AnyIO markers are skipped because the two plugins conflict; revisit only if a
  wall is hit.

## Consequences

- **Easier:** pure logic is tested without a database; integration tests
  exercise real Postgres behavior; provider calls are deterministic.
- **Harder:** Testcontainers needs Docker in CI; E2E requires a running stack.
- **We now live with:** three test tiers with distinct commands, all surfaced
  through `just`.

## Alternatives considered

- **`@testing-library/vue`** — dormant since 2024.
- **Mocking the ORM layer** — misses the behavior most likely to break.
- **A shared cloud database in CI** — slow, stateful, and flaky.
- **Cypress** — Playwright was chosen for its runner and multi-browser support.
