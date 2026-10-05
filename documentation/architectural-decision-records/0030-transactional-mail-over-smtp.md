# ADR-0030: Transactional mail goes out over SMTP, caught by Mailpit in development

- **Status:** Accepted
- **Date:** 2026-10-04
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

The application sends password-reset mail through SuperTokens' built-in SMTP
transport, with Mailpit catching every message in development, so no
development machine ever sends real email.

## Context

Forgot password is the first feature that needs to send mail, and the project
had no email infrastructure at all. Something had to choose the transport, the
sender, and what happens to mail in development.

There is a trap unique to this vendor. SuperTokens registers the reset endpoints
whether or not email is configured, and its default delivery posts the reset
link to SuperTokens' own service and swallows every exception. An unconfigured
deployment therefore answers a reset request with success and sends nothing —
which looks identical to a working one. "Fail loudly when unconfigured" is code
this project has to write, not SDK behaviour.

## Decision

- Send through SuperTokens' `SMTPService`, configured from `Settings`, and
  passed to `emailpassword.init(email_delivery=…)`. The SDK owns the transport
  and the reset template; no Python email library is added.
- The settings are generic SMTP (`smtp_host`, `smtp_port`, `smtp_username`,
  `smtp_password`, `smtp_from_name`, `smtp_from_email`, `smtp_secure`), so
  choosing a provider is a configuration change, not a code change.
- **Mailpit catches development mail.** It runs as a dev dependency in
  `compose.yaml` with its SMTP port and its HTTP API published. Real email is
  never sent from a development machine.
- **Resend** is the intended production provider, recorded as a decision only:
  nothing Resend-specific enters the code, because the settings are plain SMTP.
- An empty `smtp_host` or `smtp_from_email` installs a delivery service that
  **raises** on send, replacing the SDK's silent default. A reset attempt on an
  unconfigured deployment is a visible error, not a quiet no-op.

## Consequences

- **Easier:** one transport and one template, both maintained by the vendor; a
  provider swap is seven environment variables; the reset flow is testable
  because Mailpit exposes the captured message over HTTP.
- **Harder:** `smtp_host` differs by run mode — `localhost` on the host,
  `mailpit` in Compose — so it is set per environment rather than assumed.
- **We now live with:** a new class of secret (`smtp_password`) governed by
  ADR-0009; the `website_base_path` value is load-bearing, because the reset
  link is built from `FRONTEND_URL` plus that path.

## Alternatives considered

- **A custom `send_email` callback** — the built-in transport already does this;
  taking it over means reimplementing formatting and deliverability for no gain.
- **A Python email library (e.g. `smtplib` directly)** — duplicates what the SDK
  provides and re-opens template ownership.
- **No dev catcher, send to a real address** — rejected outright: a development
  machine must not be able to mail arbitrary people, which is exactly the abuse
  a reset endpoint invites.
- **A bare SMTP sink instead of Mailpit** — a sink proves a connection but not
  the message; Mailpit's HTTP API lets a test read the body and extract the
  token.
