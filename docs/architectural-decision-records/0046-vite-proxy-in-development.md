# ADR-0046: Vite's proxy fronts development; Caddy is the self-host front door

- **Status:** Accepted
- **Date:** 2026-10-06
- **Deciders:** Rey Obejero
- **Supersedes:** ADR-0025, ADR-0026
- **Superseded by:** —

## TL;DR

Development gets its single origin from Vite's dev proxy and runs either
natively or in Compose; Caddy is the self-host front door and is not part of
development.

## Context

The application requires one origin: the SuperTokens session cookie is httpOnly
and same-site, so the browser must send it to the API without any cross-origin
handling.

ADR-0025 and ADR-0026 answered that by running the production Caddy container in
development, on `http://localhost`, so the reverse-proxy configuration was
exercised daily. That fixed a real bug — a `strip_prefix /api` that only the
Vite proxy had masked — but it made every `just development` run a reverse proxy
whose only development-specific job was to forward to the SPA and the API.

The single-origin requirement does not name Caddy. Vite's dev proxy already
serves the SPA and forwards `/api` to the API on one origin, which is why it is
built into Vite and webpack-dev-server. The proxy is a serving concern; it
belongs where pages are actually served.

There are two production setups: self-hosted (Compose on a server you run) and
IaaS (managed cloud services, later). Development is neither.

## Decision

- **Native development is the default** (`just development`): the datastores run
  in Compose (as `just dependencies`), and the API and the SPA run on the host.
  The browser origin is `http://localhost:5173`; Vite proxies `/api` to the API
  on `:8000`. No reverse proxy.
- **Containerized development** (`just development-containerized`) runs the whole
  stack in `infrastructure/docker/compose.dev.yaml`, still without a reverse
  proxy. Vite's container is the published port, and its proxy target is the
  `api` service, so the app is single-origin at `http://localhost:5173`.
- **Self-hosted production** (`infrastructure/docker/compose.selfhost.yaml`) runs
  the API from its image and the built SPA behind Caddy. Caddy serves the static
  build and proxies `/api` to the API; it is the only service that publishes a
  host port.
- `compose.host-deps.yaml` is removed. The development file publishes the
  datastore ports itself, because reaching them from the host is a development
  concern. The self-hosted file publishes only Caddy.
- `API_BASE_URL` and `FRONTEND_URL` are the browser origin in every setup —
  `http://localhost:5173` in development, the Caddy address when self-hosted.
  They must match, or SuperTokens treats the session cookie as cross-site.
- Social sign-in registers a development callback at
  `http://localhost:5173/authentication/callback` alongside the production one.
  Google permits up to 100 redirect URIs per client, so the extra entry is free.
- `flush_interval -1` on the `/api` route is removed. Caddy's `reverse_proxy`
  and Go's `net/http/httputil` flush `text/event-stream` responses and responses
  with unknown `Content-Length` immediately regardless of the setting, so it was
  never doing anything for streaming. Its one unique effect — continuing a
  backend request after the client disconnects — is not wanted.

## Consequences

- **Easier:** the daily loop has one fewer moving part and no port 80. Reload is
  native in the default lane. Caddy is exercised by the self-hosted setup, which
  is also what the level-3 end-to-end suite runs, so proxy drift is still caught
  — in the place the proxy actually serves, rather than by running it daily.
- **Harder:** the development origin is a port rather than port 80, so the OAuth
  callback is registered per origin. A `strip_prefix` regression would not be
  caught by `just development`; it would be caught by the self-hosted e2e run.
- **We now live with:** two Compose files, because a service cannot be the Vite
  dev server and the built Caddy image in one file. `compose.dev.yaml` and
  `compose.selfhost.yaml` are peers, and profiles are reserved for optional
  extras.

## Alternatives considered

- **Keep Caddy in development (ADR-0025/0026)** — rejected. It is an unusual
  daily cost for a routing bug that the self-hosted setup now catches, and it
  forced every development origin to be port 80.
- **No proxy and cross-origin requests** — rejected. Cross-origin needs CORS and
  a `SameSite=None` cookie, and the latter requires HTTPS. The dev proxy keeps
  the guarantee without either.
- **`ai-chat.localhost` with `mkcert`** — rejected; see ADR-0025 for the two
  independent Public Suffix List and SuperTokens walls.
- **A static SPA build in development** — rejected; it turns every UI edit into a
  rebuild, which is the cost ADR-0017 was avoiding.
