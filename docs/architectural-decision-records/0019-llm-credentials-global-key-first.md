# ADR-0019: A shared LLM key ships first, BYOK comes later

- **Status:** Accepted
- **Date:** 2026-09-22
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

The application runs on one server-held OpenRouter key with a provider-enforced
spend cap, and per-user "bring your own key" is designed for but deferred.

## Context

The application is deployed publicly with open signups, so a shared key is a
shared cost that any registered account can spend. At the same time, the
project's purpose as a portfolio piece means the first thing a visitor should be
able to do is ask a question — requiring them to supply their own API key first
would defeat the demo. The credential model therefore has to trade cost exposure
against first-use friction, and the choice is hard to reverse once users are
storing keys.

## Decision

- Ship one server-held OpenRouter key, provided only through the environment
  (ADR-0009).
- Use a dedicated OpenRouter key with a USD credit limit and a monthly reset, so
  the provider rejects requests before upstream spend once the cap is reached.
- Layer per-user request-rate limiting and a durable token quota on top, since
  the cap is global rather than per-user.
- Resolve the provider through the `llm` service so a user-specific credential
  can be preferred later without touching callers.
- When BYOK lands: a per-user credential row with the key encrypted at rest
  using a server-side master key, never returned to the client, plus a Settings
  screen to add, validate, and remove it.

## Consequences

- **Easier:** zero-friction first use; one key to rotate; a hard dollar ceiling
  that does not depend on our own code being correct.
- **Harder:** the shared budget is exposed to every signup, so rate limiting and
  the quota are prerequisites to deploying, not follow-up work.
- **We now live with:** rotating the key is a redeploy, and BYOK work is
  additive but not free — encryption, validation, and a settings surface still
  have to be built.

## Alternatives considered

- **BYOK first** — no shared cost, but it blocks the demo and forces
  encryption-at-rest and a settings UI before the first reply works.
- **A shared key with no cap** — the failure mode this decision exists to
  prevent.
- **Managed per-user keys via OpenRouter's Management API** — enforces per-user
  spend at the provider, but couples every account to OpenRouter and is more
  integration than this stage needs.
- **A shared key only, never BYOK** — simplest, but caps the project's feature
  story and leaves power users unserved.
