# ADR-0009: Typed settings with env-only secrets

- **Status:** Accepted
- **Date:** 2026-09-22
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Configuration is a typed `Settings` object read at startup; secrets exist only
as environment variables and never enter the repository.

## Context

The app runs in several environments (local, CI, deployed) with different
credentials for Postgres, SuperTokens, OAuth providers, and later the LLM
provider. A sibling project once committed a service's settings file and burned
its secrets, so the cost of a leak here is not hypothetical.

## Decision

- `pydantic-settings` defines a typed `Settings` class, loaded once at startup
  through a cached accessor.
- `.env` is gitignored and used locally; a committed `.env.example` carries
  placeholders so a fresh clone bootstraps.
- Secrets are injected as environment variables in Docker and CI; non-secret
  configuration may have typed defaults.
- `gitleaks` runs in the pre-commit hook and in a CI job.
- Each new secret requires both a `Settings` field and an `.env.example` entry.

## Consequences

- **Easier:** misconfiguration fails at startup with a typed error; the set of
  required variables is discoverable from `.env.example`.
- **Harder:** rotating a secret means updating the environment and redeploying.
- **We now live with:** any secret in the repository is a bug, and the scanning
  hook is part of the definition of done.

## Alternatives considered

- **`os.environ` with `python-dotenv`** — untyped and unchecked.
- **Committed config files** — the failure mode this decision exists to prevent.
- **A secrets manager (Vault, cloud KMS)** — real value, but premature for a
  single service; revisit when multi-environment rotation matters.
