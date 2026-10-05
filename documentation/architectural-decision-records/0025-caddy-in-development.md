# ADR-0025: Caddy fronts development, on plain `http://localhost`

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Development is served at `http://localhost` (port 80, plain HTTP) by the same
Caddyfile as production, with no certificate to install.

## Context

ADR-0016 and ADR-0017 both assumed development ran natively behind Vite's proxy,
with the SPA on `:5173` and the API on `:8000`. That assumption had a cost: the
production proxy configuration was never exercised in development, so it silently
drifted. `strip_prefix /api` in the Caddyfile broke all three path expectations
in the application — the `/api/v1` router, SuperTokens' `/api/auth` gate, and the
rate limiter's path prefix — and nothing detected it, because the only path ever
exercised was the Vite proxy, which happened to be correct.

Running Caddy during development removes the second code path, so the deployed
routing is the routing that gets used.

The open question was the hostname. A distinctive development host
(`https://ai-chat.localhost` with `mkcert`) is the conventional answer, and it is
not available here.

## Decision

- The development origin is `http://localhost`, port 80, no TLS.
- Caddy serves development and production from one Caddyfile; only the site
  address differs. Production uses a real domain and obtains an ACME certificate
  automatically.
- `API_BASE_URL` and `FRONTEND_URL` are both `http://localhost` in development.
  Both must be loopback for SuperTokens' insecure-cookie path.
- Social sign-in registers `http://localhost/authentication/callback` with each
  provider — the SPA route, because the web SDK sends its `frontendRedirectURI`
  as the provider's redirect URI.
- No certificate tooling (`mkcert`, `libnss3-tools`) in the development setup.

## Consequences

- **Easier:** development and production share one routing configuration, so
  proxy bugs surface immediately instead of at deploy. No browser warning, no
  trust store, no extra setup step.
- **Harder:** port 80 on the host, so Caddy cannot coexist with anything else
  bound there. Redirect URIs must be registered with the development origin
  alongside production ones.
- **We now live with:** social providers receive plain-HTTP redirects from
  `localhost`, which works only because providers special-case that exact host.

## Alternatives considered

- **`ai-chat.localhost` with `mkcert`** — two independent walls. Google requires
  the redirect URI host TLD to be in the Public Suffix List; `localhost` is not
  in it (verified against the live list: 16,501 entries, no `localhost`), and the
  whitelist carve-out for `localhost` is an exact host match that does not extend
  to subdomains. Independently, SuperTokens only permits a non-secure session
  cookie when the website and API domains are both loopback or an IP;
  `ai-chat.localhost` is neither, so HTTPS plus a secure cookie would be required
  anyway. A certificate does not fix either.
- **`.test`, `.local`, `.example`, `.invalid`** — all RFC 6761 reserved TLDs,
  all rejected by the same Public Suffix List rule.
- **Free TLDs (`.tk`, `.ml`)** — Freenom ended free registration in 2023.
- **A different port (8000, 8080)** — 8000 is claimed by `just back-end` and the
  e2e API; 8080 works but forces the port into every URL and every registered
  redirect URI. Nothing in the repository claims 80, so the collision disappears
  entirely and the browser omits the port.
- **Leaving development on the Vite proxy** — rejected. That is what let
  `strip_prefix` sit in the Caddyfile undetected.