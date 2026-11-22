# ADR-0033: Social sign-in end-to-end tests run against a local OIDC provider

- **Status:** Accepted
- **Date:** 2026-10-04
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

The social sign-in flow is covered end to end against a real, local OIDC
provider started as a Playwright `webServer`, so discovery, JWKS verification
and the token exchange all run without contacting Google or GitHub.

## Context

Social sign-in has four hops, and only one is in the browser:

```
browser → app            click "Continue with <provider>"
app      → provider      build the authorization URL
browser  → provider      the user authenticates there
provider → app            redirect with a code
app      → provider      exchange the code, fetch userinfo   ← server-side
```

Intercepting the browser hop with `page.route()` mocks one hop and leaves the
last one failing: the back end redeems the authorization code itself and would
call the real provider with a fabricated code. So a fake **provider** is
required, not a fake navigation.

## Decision

- Run a local OIDC provider as another deterministic Playwright `webServer`
  entry, alongside the mock model provider — the pattern ADR-0023 established.
- It implements the parts the SDK actually depends on: the discovery document,
  a JWKS endpoint, an RS256-signed id_token, and a token exchange. It is not an
  interactive login UI — `/authorize` issues a code immediately — which is what
  keeps the suite deterministic.
- It is steered per test through a small control endpoint (which email to
  return, whether to omit it, whether to refuse consent), so the branches are
  reproducible on demand.
- The provider is written with Node built-ins, so the suite gains no dependency.
- The provider is registered through the same gated test identity provider as
  ADR-0029, which cannot be enabled in a production environment.

## Consequences

- **Easier:** every hop is real, the paths that cannot be produced by hand
  (consent refused, no email shared) become ordinary tests, and the suite needs
  no OAuth credentials or outbound network.
- **Harder:** the suite gains another shared service; the specs that steer the
  provider must not run concurrently, so they are serialised.
- **We now live with:** a test provider whose id_token signature is real and
  therefore actually exercises the SDK's JWKS verification.

## Alternatives considered

- **`page.route()` interception** — rejected. The code exchange is server-side,
  so mocking the browser hop leaves the back end calling the real provider.
- **A hand-written stub that skips discovery or JWT validation** — rejected;
  those are exactly the parts that break when a provider's behaviour changes.
- **A full framework (Keycloak, a real Google project)** — rejected as too
  heavy for one flow, and, for the real provider, non-deterministic and
  credential-bound.

## What this does not cover

This proves the **flow**, not the **provider configuration**. Whether the
redirect URIs are registered correctly, the client secrets are current, and the
scopes still return an email can only be found against the real provider. Those
are a separate, manual or scheduled check; this suite deliberately does not
pretend to substitute for it.
