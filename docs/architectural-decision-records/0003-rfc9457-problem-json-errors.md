# ADR-0003: Errors use RFC 9457 `application/problem+json`

- **Status:** Accepted
- **Date:** 2026-09-22
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Every error the API returns is an RFC 9457 problem document with a stable
machine-readable `code`, produced by one set of handlers.

## Context

The API mixes our own domain failures, request-validation failures, and errors
raised inside the auth vendor (SuperTokens). Without a single envelope the
client has to special-case each source, and error handling leaks into every
layer.

## Decision

- Domain errors subclass `AppError`; the service layer raises them and never
  imports `fastapi` or `HTTPException`.
- Handlers in `shared/exceptions.py` serialize every error as
  `application/problem+json` with `type`, `title`, `status`, `detail`,
  `instance`, and a `code` extension member. Validation errors add an `errors`
  extension.
- SuperTokens' own 401s are translated into the same envelope through its
  `on_unauthorised` hook.
- Per-class dereferenceable `type` URIs are a future, additive upgrade.

## Consequences

- **Easier:** the client parses one shape; adding an error class is a subclass
  plus a handler.
- **Harder:** middleware-raised responses sit outside the handlers and must
  build the same body themselves.
- **We now live with:** `type` is `about:blank` for everything until the URI
  upgrade lands; `code` is the stable identifier in the meantime.

## Alternatives considered

- **Bare `HTTPException`** — inconsistent bodies and status/title mapping.
- **A bespoke envelope** — reinvents a standard the client can't reuse.
- **Errors as domain objects in responses** — leaks internals and couples the
  client to server types.
