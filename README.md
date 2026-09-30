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

## Features

### Authentication

![Sign-In View](./documentation/assets/screenshots/authentication/sign-in.png)
