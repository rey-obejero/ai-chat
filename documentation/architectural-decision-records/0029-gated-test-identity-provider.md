# ADR-0029: The application carries a gated stand-in identity provider for tests

- **Status:** Accepted
- **Date:** 2026-10-04
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

The backend can register a synthetic OIDC provider that exists only for the
end-to-end suite, and three independent conditions must all hold before it is
registered, so a real deployment cannot be tricked into trusting an unverified
identity provider.

## Context

The social sign-in flow (ADR-0028) needs an end-to-end test that exercises the
real redirect-and-callback path, not a mock that skips the browser round trip.
That requires a provider the suite controls: one that can be started quickly,
driven programmatically, and made to fail on demand.

A test provider is a security liability if it can appear outside tests. An
OIDC provider is defined by a discovery URL; if one can be registered by setting
a flag and a URL, then whoever can set those can point the application at an
identity provider they operate and mint identities for arbitrary users. This is
the classic "test backdoor" failure.

## Decision

The backend registers a provider with the fixed id `test-idp` **only** when all
three of the following hold (`_test_provider`, `adapter_supertokens.py`):

1. `TEST_IDP_ENABLED` is explicitly true — not inferred, not defaulted on.
2. Both a client id and a client secret are present.
3. The discovery base URL's host is one of `idp.test`, `localhost`, or
   `127.0.0.1`.

The third condition is the load-bearing one: the other two are ordinary
settings, but a URL pointing anywhere else is refused, so an operator cannot
aim the application at a real provider by flipping the switch. The guard is
code, not a comment, and each condition has its own unit test.

The provider is registered through the same `_providers` path as Google and
GitHub, so the UI's provider list and the core cannot disagree about which
buttons exist.

## Consequences

- **Easier:** the social flow can be driven end to end against a real,
  inspectable provider without any vendor account.
- **Harder:** the suite must run something on one of the three permitted hosts.
  Because `localhost` resolves to the API container in the full-stack Compose
  setup (ADR-0026), a same-container provider is the natural shape.
- **We now live with:** `TEST_IDP_*` settings exist in `Settings` but are
  deliberately absent from `.env.example`. The switch's point is that it is not
  something to reach for; documenting it invites exactly the accident the guard
  prevents.

## Alternatives considered

- **A mock that intercepts the HTTP calls** — rejected. It skips the callback
  and session-establishment path, which is the part worth testing.
- **A real third-party account (a dedicated Google project)** — rejected. It
  couples CI to an external service's availability and credentials, and cannot
  be made to fail deterministically.
- **Gate on the environment name (`ENV=test`)** — rejected. The environment
  name is one variable and is set by whoever is running the stack; it is a
  weaker guarantee than requiring a host the operator does not control.
