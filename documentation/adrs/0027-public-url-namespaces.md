# ADR-0027: `/authentication` and `/application` partition the public URL space

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Public URLs are namespaced: `/authentication/*` is the signed-out surface and
`/application/*` is the authenticated one.

## Context

The routes were flat: `/sign-in`, `/sign-up`, `/auth/callback`,
`/conversations`. Nothing in the URL said which part of the application a path
belonged to, so adding a signed-out feature or a signed-in one meant choosing a
name with no convention behind it. There was also no 404 route, so an unknown URL
rendered a blank page — invisible until the application was publicly reachable.

SuperTokens introduces a second namespace that *looks* related and is not:
`/api/auth` is the SDK's own API path.

## Decision

| Surface | Prefix |
|---|---|
| Signed out | `/authentication/*` — `sign-in`, `sign-up`, `callback` |
| Signed in | `/application/*` — `conversations`, and everything added later |
| SDK API | `/api/auth` — SuperTokens' own, outside both namespaces |

- Route **names** are the stable contract. Navigate by name, not by path string,
  so the next path change is a one-line edit in the route table rather than a
  grep across views and e2e specs.
- `/application` is a grouping route with no component and
  `meta.requiresAuth: true`. Vue Router merges parent `meta` into every child, so
  one declaration covers the whole authenticated surface, including routes not
  written yet.
- There is a catch-all `not-found` route.

**`redirectTo` is user-controllable input and must be validated.**
The post-sign-in redirect travels in the query string. It is only same-origin
today because the sole producer is `to.fullPath`, and that stops being true the
moment anyone can hand-craft a URL. `//evil.example` is protocol-relative and the
router will follow it, so `safeRedirect` rejects anything that is not a
same-origin absolute path, including `\`-prefixed values that browsers normalise
to the protocol-relative form.

**`/api/auth` is SuperTokens' API path and is deliberately not moved into
`/authentication`.** The OAuth provider consoles point at
`{api_domain}/api/auth/callback/{provider}`, which SuperTokens' backend handles
before forwarding the browser to the SPA route `{origin}/authentication/callback`.
The two look alike and are not. A refactor that "tidied" `/api/auth` under the
authentication namespace would break provider sign-in silently — the redirect URI
registered in Google and GitHub would simply stop matching.

## Consequences

- **Easier:** the authenticated boundary is visible in the URL, so a new feature
  has an obvious home. An unknown URL renders a 404 instead of a blank page.
  Renaming a path touches one file.
- **Harder:** existing links and bookmarks change. Every hardcoded path in views
  and e2e specs had to move.
- **We now live with:** two prefixes to remember, and a `redirectTo` contract that
  needs a validator at every consumption point.

## Alternatives considered

- **Leave the routes flat** — rejected. It leaves the naming convention implicit,
  which is how `/auth/callback` and `/authentication/callback` both end up
  plausible a year apart.
- **Rename `/api/auth` too** — rejected, and dangerous. It is the SDK's path, and
  it is the value registered in the provider consoles.
- **Validate the redirect in the guard rather than at the consumer** — the guard
  only *produces* the value; the view is what consumes it, so that is where the
  check belongs.