# ADR-0031: Password reset never reveals whether an account exists

- **Status:** Accepted
- **Date:** 2026-10-04
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

The reset flow answers identically whether or not an account exists, revokes
every session when a password is set, and treats the reset token as a bearer
secret that never reaches a log.

## Context

A password reset is where an application is most tempted to leak, and where the
leaks are most valuable. Three properties have to hold, and each is easy to undo
later for what looks like a good reason.

The vendor gets the first one right by default: the reset-token endpoint returns
the same result for an unknown address as for a real one. It does **not** get
the second right — nothing in the SDK revokes sessions on reset — and the third
is a property of our own URL handling and the reverse proxy's logs, not the SDK.

## Decision

- **No enumeration.** The request endpoint's HTTP response is identical for a
  known and an unknown address, and the front end shows one fixed confirmation
  ("If that address has an account, we've sent a link"). Nothing branches on
  whether the account exists, including the SDK's `PASSWORD_RESET_NOT_ALLOWED`
  status, which collapses into the same confirmation.
- **Revoke all sessions on password change.** The SDK's password-update function
  is wrapped so that a successful password change ends every session for the
  user. Without it, a reset does not evict an attacker already signed in, which
  is the point of resetting. The capability sits behind the `UserDirectory`
  port (ADR-0010).
- **The token is a bearer secret.** The reset view reads it, strips it from the
  URL on mount, and never renders it. The reverse proxy sends
  `Referrer-Policy: no-referrer` and redacts the `token` query parameter from
  access logs. Because the SDK reads the token from the URL at submit time, the
  captured value is re-injected into the request body rather than restored to
  the URL.
- **The routes are public and fixed by the vendor.** The request view is
  `/authentication/forgot-password` and the reset view is
  `/authentication/reset-password` — the second is the path the emailed link
  targets, so it is not ours to rename. Both are `requiresAuth: false`
  explicitly rather than by inheritance (ADR-0027).
- **A successful reset does not sign the user in.** The SDK returns no session,
  so the UI sends them to sign-in instead of assuming one.

## Consequences

- **Easier:** one rule to audit — nothing in the flow differs by account
  existence — and a reset that actually accomplishes its security purpose.
- **Harder:** the confirmation copy must stay vague, and the token handling must
  survive refactors that look cosmetic. The revocation override wraps a vendor
  function, so a vendor change to that function is a place to check.
- **We now live with:** the no-referrer policy applies to the whole origin, and
  Caddy's access log no longer records the real value of a `token` query
  parameter anywhere. The single-use property is the SDK's; a used token is
  rejected on reuse.

## Alternatives considered

- **Tell the user when an address is unknown** — rejected; it turns the endpoint
  into an account-existence oracle, which is the enumeration this ADR prevents.
- **Do not revoke sessions** — rejected; a reset that leaves the attacker's
  cookie valid is theatre.
- **Keep the token in the URL and rely on HTTPS** — rejected; it still lands in
  history, the address bar, and any `Referer`, and HTTPS does not help with
  server-side logs.
- **Filter the token only in the application, not the proxy** — rejected; the
  SPA is served through the proxy, so the proxy is where the URL is logged.
