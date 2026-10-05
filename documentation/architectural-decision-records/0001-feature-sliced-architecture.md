# ADR-0001: Business logic is organized as vertical feature slices

- **Status:** Accepted
- **Date:** 2026-09-22
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Features are vertical slices with explicit public APIs; only cross-cutting
infrastructure is shared horizontally.

## Context

The app grows by adding capabilities (auth, conversations, documents, retrieval,
skills, tools), and each capability touches models, schemas, routes, and tests
at once. A layer-first layout — `controllers/`, `services/`, `models/` — makes
every change span several directories and lets unrelated modules reach into each
other, so boundaries erode as the project grows.

## Decision

- Back-end: `back-end/src/ai_chat/<feature>/`, front-end:
  `front-end/src/features/<feature>/`.
- Each feature exposes an explicit public API — `__init__.py` on the back-end,
  `index.ts` on the front-end. Nothing imports a feature's internals across a
  boundary.
- Cross-cutting infrastructure is horizontal and lives in `shared/`
  (back-end) and `app/` + `lib/` (front-end). It holds no domain rules.
- `main.py` owns the `/api/v1` router prefix; SuperTokens routes live under
  `/api/auth`.
- Tests mirror the slice, split by kind: `tests/<feature>/{unit,integration}/`.

## Consequences

- **Easier:** adding or removing a feature is contained in one directory;
  imports have a stated direction; a feature can be tested in isolation.
- **Harder:** genuine cross-feature needs must go through public APIs, which
  sometimes means an extra indirection.
- **We now live with:** the boundary is enforced by convention and review, not
  by tooling; shared utilities risk becoming a dumping ground if not policed.

## Alternatives considered

- **Layer-first layout** — every change spans several directories and module
  boundaries decay over time.
- **Single flat package** — no isolation; everything can import everything.
- **Package-by-type with a service layer per type** — meaningful boundaries only
  for CRUD, not for capabilities.
