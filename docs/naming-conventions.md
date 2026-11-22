# Naming Conventions

A short reference for the names this codebase uses — URLs, query parameters,
routes, directories, and imports. It records the convention as implemented so
new code has one place to check. It is not an ADR; the decisions themselves live
in `architectural-decision-records/`.

## API

- The `/api/v1` prefix is owned by `backend/src/ai_chat/main.py`; feature
  routers add only their resource segment (for example `/conversations`,
  `/models`, `/usage`).
- Resource segments are **plural**: `/conversations`, `/models`, `/preferences`.
- Path parameters are **snake_case** and end in `_id`:
  `{conversation_id}`, `{message_id}`.
- A verb appears only in the **final** path segment, and only for streaming or
  action operations: `POST /conversations/{conversation_id}/messages/{message_id}/edit`
  and `.../regenerate`. Collection and item operations use HTTP methods, not
  verbs.
- `PATCH` for partial updates; `PUT` only for full replacement.
- `GET /api/v1/health` and `GET /api/v1/ready` are the liveness/readiness pair.

## Query parameters

The observed convention is:

- **camelCase** where the parameter mirrors a link the auth vendor generates
  (`redirectTo`, `tenantId`) — renaming these would break the vendor's URL
  contract.
- **lowercase single words** otherwise (`token`, `reset`).

For new parameters, follow the same rule: preserve the vendor's spelling when
the parameter is part of its contract, otherwise use a lowercase single word
(or camelCase only if it already mirrors a vendor name).

## Frontend routes

- URL namespaces: `/auth/*` is the signed-out surface, `/app/*` the
  authenticated one. `/unavailable` is public (the retry screen for an
  unreachable API).
- Route **names** are the stable contract. They are kebab-case
  (`sign-in`, `reset-password`, `not-found`) and code should navigate by name,
  not by hand-built path, so a path change stays a one-line edit in the route
  module.
- The route table lives in `frontend/src/app/routes/` (split by surface) and is
  composed by `frontend/src/app/router/index.ts`.
- Unmatched URLs render the `not-found` route (`/:pathMatch(.*)*`).

## Repo layout

- Root directories are lowercase single words: `frontend/`, `backend/`, `e2e/`,
  `docs/`, `infrastructure/`. Hyphenated variants (`front-end/`, `back-end/`) are
  retired.
- The Python package uses underscores (`ai_chat`) because the language requires
  importable identifiers.
- npm package names keep the scoped form (`@ai-chat/frontend`).

## Imports

- No feature barrels: import concrete files directly. A feature's `index.ts`
  is not a public surface; `@/features/<feature>/<file>` is. This is Bulletproof
  React's current guidance.
- Cross-feature composition happens at the **app layer**
  (`frontend/src/app/`), not by one feature importing another's internals.

## Where the old convention differed

Earlier code used feature barrels, `/authentication` and `/application` URL
namespaces, and the old `documentation` directory (now `docs/`). Those names
are retired, so references to them in history are expected.
