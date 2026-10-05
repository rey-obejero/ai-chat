# ADR-0006: FastAPI is the back-end framework

- **Status:** Accepted
- **Date:** 2026-09-22
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

The API is a FastAPI (ASGI) application.

## Context

The back-end serves a JSON API, streams model output over SSE, and is built as
an async app talking to Postgres and several external services. It also needs
first-class request validation and generated API documentation without extra
work.

## Decision

- FastAPI on uvicorn (ASGI).
- Pydantic v2 validates at the boundary; domain rules live in services.
- Dependency injection provides database sessions, the current user, and
  configuration.
- OpenAPI is generated from the route and schema definitions.

## Consequences

- **Easier:** async-native request handling; typed schemas double as validation
  and documentation; dependency injection keeps cross-cutting concerns out of
  route bodies.
- **Harder:** middleware and dependency lifetimes are distinct concepts that
  must be understood to place logic correctly.
- **We now live with:** the OpenAPI document is a public surface and should not
  drift from the schemas.

## Alternatives considered

- **Django + DRF** — heavier, sync-first, more ceremony than this API needs.
- **Flask** — no async, no built-in DI, weaker schema story.
- **Litestar** — capable, smaller ecosystem and less familiar.
