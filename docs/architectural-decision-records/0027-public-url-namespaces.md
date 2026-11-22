# ADR-0027: `/auth` and `/app` partition the public URL space

- **Status:** Accepted
- **Date:** 2026-10-03
- **Amended:** 2026-11-22 — the namespaces were shortened to `/auth` and `/app`.
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Public URLs are namespaced: `/auth/*` is the signed-out surface and `/app/*` is
the authenticated one.

## Context

The routes were flat: `/sign-in`, `/sign-up`, a callback and `/conversations`.
Nothing in the URL said which part of the application a path belonged to, so
adding a signed-out feature or a signed-in one meant choosing a name with no
convention behind it. There was also no 404 route, so an unknown URL rendered a
blank page — invisible until the application was publicly reachable.

SuperTokens introduces a second namespace that *looks* related and is not:
`/api/auth` is the SDK's own API path.

## Decision

| Surface | Prefix |
|---|---|
| Signed out | `/auth/*` — `sign-in`, `sign-up`, `callback` |
| Signed in | `/app/*` — `conversations`, and everything added later |
| SDK API | `/api/auth` — SuperTokens' own, outside both namespaces |

- Route **names** are the stable contract. Navigate by name, not by path string,
  so the next path change is a one-line edit in a route module rather than a
  grep across views and e2e specs.
- The route table is split by surface into thin modules under `app/routes/`
  (`auth`, `app`, `errors`); each route lazy-loads its view, so no surface pays
  for another's screens.
- `/app` is a grouping route with no component, `meta.requiresAuth: true`, and a
  redirect to `conversations`. Vue Router merges parent `meta` into every child,
  so one declaration covers the whole authenticated surface, including routes
  not written yet.
- Public routes carry `meta.requiresAuth: false` explicitly rather than relying
  on a default. There is a catch-all `not-found` route, and `/unavailable` for a
  failed session check.
- There are no `features/*/index.ts` barrels. A route imports the view file it
  renders, which is what makes the per-surface lazy loading above truthful.

**`redirectTo` is user-controllable input and must be validated.**
The post-sign-in redirect travels in the query string. It is only same-origin
today because the sole producer is `to.fullPath`, and that stops being true the
moment anyone can hand-craft a URL. `//evil.example` is protocol-relative and the
router will follow it, so `safeRedirect` rejects anything that is not a
same-origin absolute path, including `\`-prefixed values that browsers normalise
to the protocol-relative form.

**`/api/auth` is SuperTokens' API path and is deliberately outside both
namespaces.** The two paths share their last segment and nothing else: `/api/auth`
is where the SDK exposes its endpoints, and `/auth` is where the SPA's screens
live. Keeping the API under `/api` is what separates them.

The provider console is given the **SPA** route — `{origin}/auth/callback`.
The web SDK sends its `frontendRedirectURI` as the provider's redirect URI, and
this app does not pass `redirectURIOnProviderDashboard` to override it, so the
browser returns to the SPA, which hands the code to `/api/auth/signinup`. A
refactor that "tidied" the one into the other would break provider sign-in
silently: the URI registered with Google and GitHub would stop matching, and the
failure surfaces at the provider rather than in the app.

## Consequences

- **Easier:** the authenticated boundary is visible in the URL, so a new feature
  has an obvious home. An unknown URL renders a 404 instead of a blank page.
  Renaming a path touches one route module.
- **Harder:** existing links and bookmarks change. Every hardcoded path in views
  and e2e specs had to move.
- **We now live with:** two prefixes to remember, and a `redirectTo` contract that
  needs a validator at every consumption point.

## Alternatives considered

- **Leave the routes flat** — rejected. It leaves the naming convention implicit,
  so a signed-out callback and a signed-in screen both end up plausible names a
  year apart.
- **Rename `/api/auth` too** — rejected, and dangerous. It is the SDK's path, and
  it is the value registered in the provider consoles.
- **Validate the redirect in the guard rather than at the consumer** — the guard
  only *produces* the value; the view is what consumes it, so that is where the
  check belongs.
