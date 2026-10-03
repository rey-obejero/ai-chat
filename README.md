# AI Chat

![Conversations View](./documentation/assets/screenshot.png)

## Technologies

| Area               | Technology                 |
| ------------------ | -------------------------- |
| Back-End           | FastAPI, Python            |
| Front-End          | Vue 3, Vite, TypeScript    |
| UI                 | PrimeVue 4, TailwindCSS V4 |
| Authentication     | SuperTokens                |
| Database           | PostgreSQL, SQLAlchemy     |
| Package Management | uv, pnpm                   |
| Containerization   | Docker Compose, Docker     |
| Reverse Proxy      | Caddy                      |

## Topology

```mermaid
flowchart TB
  browser(["Browser"])
  caddy["Caddy"]
  vue["Vue"]
  fastapi["FastAPI"]
  supertokens["SuperTokens"]
  postgres[("PostgreSQL")]
  redis["Redis"]
  llm["LLM Provider"]

  browser --> caddy
  caddy --> vue
  caddy --> fastapi
  fastapi --> supertokens
  fastapi --> postgres
  fastapi --> redis
  fastapi --> llm
```

## Getting Started

```sh
git clone <repo> && cd ai-chat
just install
just development
```

Then open <http://localhost>. That runs the whole stack in Compose — Postgres,
SuperTokens, Redis, the API, the Vite dev server, and Caddy in front of both.

```sh
just development-logs     # follow output in another terminal
just development-stop
```

There is nothing to configure for local use and no certificate to trust: the
development origin is plain HTTP (ADR-0025). Copy `back-end/.env.example` to
`back-end/.env` only if you need to change a default, such as adding an LLM key
to try a real reply.

`just dependencies` brings up just the datastores, and `just back-end` /
`just front-end` run the API and SPA on the host — useful for debugging, and
what the e2e suite uses so it can supply its own mock provider (ADR-0023).

### OAuth redirect URIs

Social sign-in is configured per provider. Register the **SuperTokens** callback,
not an SPA route:

```
http://localhost/api/auth/callback/google
http://localhost/api/auth/callback/github
```

Development and production entries coexist; Google permits up to 100 redirect
URIs per client.

## Features

### Authentication

![Sign-In View](./documentation/assets/screenshots/authentication/sign-in.png)
