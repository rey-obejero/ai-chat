# ADR-0010: SuperTokens provides authentication

- **Status:** Accepted
- **Date:** 2026-09-22
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

SuperTokens, self-hosted, provides email/password and social login behind a thin
boundary so the vendor can be replaced in one place.

## Context

The app needs multi-user accounts, email/password, Google and GitHub login,
sessions, and per-user data isolation. Building and maintaining session security
by hand is a known source of serious bugs, but adopting a hosted identity
provider adds an external dependency and cost.

## Decision

- SuperTokens self-hosted, with the `session`, `emailpassword`, and `thirdparty`
  recipes, run as a compose service alongside Postgres.
- Only `auth/adapter_supertokens.py` imports the SDK; everything else depends on
  `get_current_user_id` and the `UserDirectory` port.
- The app keeps its own `users` table (`id`, `email`) so conversations can carry
  a foreign key; the vendor's user id is the primary key.
- Provider configuration is driven by `Settings`, so a provider with no
  credentials configured is simply absent from the UI.

## Consequences

- **Easier:** proven session handling; social login without bespoke OAuth code;
  swapping providers touches one module plus the port.
- **Harder:** one more service to run, upgrade, and keep in sync with the SDK
  version; a local `users` row must exist for foreign keys.
- **We now live with:** the SDK is a hard boundary to respect — the rest of the
  code must never import it directly.

## Alternatives considered

- **Hand-rolled JWT sessions** — a security burden with no differentiating value.
- **Hosted identity (Auth0, Clerk, WorkOS)** — faster to start, adds external
  cost and a dependency; self-hosting was preferred.
- **Keycloak** — powerful and heavy for a single application.
