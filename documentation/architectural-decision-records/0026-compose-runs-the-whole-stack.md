# ADR-0026: Compose runs the whole stack, Caddy included

- **Status:** Superseded by ADR-0046
- **Date:** 2026-10-03
- **Deciders:** Rey Obejero
- **Supersedes:** ADR-0017
- **Superseded by:** ADR-0046

> **Superseded by [ADR-0046](0046-vite-proxy-in-development.md).** Compose no
> longer runs Caddy in development, and the `full` profile no longer selects a
> setup. `compose.dev.yaml` runs the containerized development stack without a
> proxy; `compose.selfhost.yaml` runs the built SPA behind Caddy. The one-shot
> `migrate` service, the healthchecks, and the "secrets stay out of the build
> context" rule remain in force.


## TL;DR

Development runs the API, the SPA, and the proxy from Compose, not from `just`
on the host, so the deployed routing is the routing that gets exercised.

## Context

ADR-0017 kept the application processes on the host because containers slow down
reload, and put Vite's proxy in front of the API in development.

That arrangement had a cost nobody had measured: the Caddyfile was never
exercised in development. It accumulated `uri strip_prefix /api`, which sends
FastAPI `/v1/health` instead of `/api/v1/health`. Every path in the application
404s behind it — the router prefix, SuperTokens' `/api/auth` gate, and the rate
limiter's path prefix. It survived because the only path ever tested was Vite's
proxy, which preserved the prefix and happened to be correct.

ADR-0016 had already predicted this: the proxy config is a deployment artifact
that can drift from the app.

ADR-0017's own reason, faster reload, is real but it is the smaller cost. Recent
work has been UI polish, and rebuild-per-edit is precisely the thing that would
hurt.

## Decision

- `infrastructure/docker/compose.yaml` defines `postgres`, `supertokens`,
  `redis`, `migrate`, `api`, `front-end`, and `caddy`.
- The front-end service runs the **Vite dev server**, not a static build.
- Caddy is the only service that publishes a host port: **port 80 and nothing
  else**. This is a security rule, not a convention.
- The API listens on 8000 inside the compose network only.
- The app services sit behind a `full` profile. CI and the e2e suite start the
  API and SPA on the host, so they compose the same file with
  `compose.host-deps.yaml`, which republishes only the dependency ports.
- A one-shot `migrate` service runs `alembic upgrade head`; `api` waits for it to
  succeed.
- Secrets stay out of the build context: `back-end/.dockerignore` excludes
  dotenv files. `.gitignore` does not apply to Docker, so this is a separate rule
  from ADR-0009.

HMR needs no configuration. With no `hmr.host` and no `clientPort`, Vite derives
the socket origin from the client script's URL, which is the page's own origin;
Caddy forwards the WebSocket upgrade. Both facts are worth keeping, because
adding either would break a working setup in a way that is hard to read.

## Consequences

- **Easier:** proxy configuration is exercised on every run, so a routing bug
  fails in development instead of at deploy. One command brings up the stack at
  one origin. Migrations run automatically on a fresh volume.
- **Harder:** no host `just back-end` / `just front-end` reload loop for the
  normal workflow. Startup waits on `pnpm install` inside the container.
- **We now live with:** uvicorn trusts `X-Forwarded-For` from any peer, and the
  rate limiter keys unauthenticated requests on exactly that header. Publishing
  the API's port would let any client spoof its address and bypass the limit
  entirely. Do not add a `ports:` entry to any service but `caddy`.

## Alternatives considered

- **Keep Vite's proxy in development** — rejected. That is what let the
  `strip_prefix` bug go unnoticed.
- **A static SPA build in the compose stack** — cheaper and closer to production,
  but it turns every UI edit into a rebuild, which is the cost ADR-0017 was
  trying to avoid. Revisit if development moves off the bind mount.
- **Publish the API on 8000 for convenience** — rejected. See the rate-limiter
  consequence above.
- **Run Caddy on the host alongside Compose** — no benefit here; the container
  needs the same network access to `api` regardless, and it removes a moving
  part.