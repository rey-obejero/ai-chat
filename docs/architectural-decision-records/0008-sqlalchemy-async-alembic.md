# ADR-0008: SQLAlchemy 2.x async with Alembic migrations

- **Status:** Accepted
- **Date:** 2026-09-22
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

The data layer is SQLAlchemy 2.x in async mode over asyncpg, with Alembic
managing schema migrations.

## Context

The API is async end to end. Blocking the event loop on database calls would
negate the reason for an async framework, and the schema will evolve across many
features, so migrations must be versioned and reversible.

## Decision

- SQLAlchemy 2.x declarative models with `Mapped` / `mapped_column`.
- `asyncpg` as the driver; `create_async_engine` and `AsyncSession`.
- Sessions are provided per request through a `get_session` dependency that
  closes them after the response.
- Alembic runs in async mode via its `env.py`; revisions are reversible and
  clearly named.

## Consequences

- **Easier:** no blocking database calls in routes; one session lifecycle; the
  schema history is explicit and reviewable.
- **Harder:** alembic autogenerate and its environment need async-aware
  configuration; eager-loading mistakes surface as runtime errors rather than
  query-time warnings.
- **We now live with:** every model change requires a migration, including the
  reversible `downgrade`.

## Alternatives considered

- **Sync SQLAlchemy in a thread pool** — worse concurrency and a second mental
  model.
- **Raw SQL with a query builder** — loses typed models and migration
  integration.
- **Tortoise ORM** — smaller ecosystem and less alignment with Alembic.
