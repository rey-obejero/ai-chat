# ADR-0004: No mapper layer between ORM models and the domain

- **Status:** Accepted
- **Date:** 2026-09-22
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

SQLAlchemy models act as the domain objects; there is no separate ORM-to-domain
mapping layer.

## Context

A common pattern keeps ORM rows and domain entities separate and maps between
them. That costs a mapper per entity plus two parallel type hierarchies, and it
only pays off when the domain model genuinely diverges from the storage shape.
For this project they are close: a conversation is a row, a message is a row.

## Decision

- SQLAlchemy ORM models are the domain layer.
- Request and response shapes stay in Pydantic schemas at the boundary.
- Conversion uses `from_attributes=True` with `model_validate()` /
  `model_dump()` rather than hand-written mappers.

## Consequences

- **Easier:** less code per entity; one type to reason about in services.
- **Harder:** changing the persistence shape can ripple into domain logic; the
  API contract now depends on discipline in the schemas, not on a mapper.
- **We now live with:** response schemas must explicitly exclude anything not
  meant to leave the server (for example a `user_id` that is implied by the
  session).

## Alternatives considered

- **Full mapper/DTO layer** — boilerplate with no second domain need to justify
  it.
- **Duplicated dataclasses** — two representations kept in sync by hand.
- **Returning ORM models directly** — leaks persistence details into the API.
