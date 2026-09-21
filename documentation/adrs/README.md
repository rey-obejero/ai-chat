# Architecture Decision Records

An ADR records one architecturally significant decision: the forces behind it,
what was chosen, and what it costs. They exist so that reviewing this project
doesn't mean reconstructing intent from a diff.

Keep them short. An ADR that takes more than two minutes to read won't get read.

## Format

Every ADR uses the same sections, in this order:

| Section | What goes in it |
| --- | --- |
| Title | `ADR-NNNN: <the decision, stated as a fact>` |
| Status | `Proposed`, `Accepted`, `Deprecated`, or `Superseded by ADR-NNNN` |
| Date | ISO date (`YYYY-MM-DD`) the ADR was written |
| Backfilled | `yes` when recording a decision made earlier; omitted otherwise |
| Deciders | Who owned the decision |
| Supersedes / Superseded by | ADR numbers, or `—` |
| TL;DR | One sentence. A reader who stops here still gets the gist. |
| Context | The situation and the forces, in plain language |
| Decision | What was chosen |
| Consequences | Bullets covering what gets easier, what gets harder, and what we now live with |
| Alternatives considered | Each option with a one-line reason it wasn't chosen |

Headings are fixed; don't invent new ones. If a section is genuinely empty,
write `—`.

## Status lifecycle

```
Proposed ──▶ Accepted ──▶ Superseded by ADR-NNNN
                 │
                 └──────▶ Deprecated
```

- **Proposed** — written down, not yet agreed.
- **Accepted** — in force; the code should match it.
- **Superseded** — replaced by a later ADR. Keep the old one for history.
- **Deprecated** — no longer true, and not replaced.

Never delete an ADR. To change a decision, write a new one that supersedes it
and update the old one's `Superseded by` field.

## Naming

`NNNN-short-slug.md` — four digits, zero-padded, sequential, never reused. The
number in the filename matches the number in the title.

Start new records from [`TEMPLATE.md`](TEMPLATE.md).

## Index

| # | Title | Status | Date |
| --- | --- | --- | --- |
| [0001](0001-feature-sliced-architecture.md) | Feature-sliced architecture | Accepted | 2026-09-22 |
| [0002](0002-monorepo-and-tooling.md) | Monorepo layout and tooling | Accepted | 2026-09-22 |
| [0003](0003-rfc9457-problem-json-errors.md) | RFC 9457 `problem+json` errors | Accepted | 2026-09-22 |
| [0004](0004-no-mapper-layer.md) | No mapper layer | Accepted | 2026-09-22 |
| [0005](0005-conversations-domain-vocabulary.md) | "Conversations" as the domain vocabulary | Accepted | 2026-09-22 |
| [0006](0006-fastapi-backend.md) | FastAPI back-end | Accepted | 2026-09-22 |
| [0007](0007-postgres-pgvector-tsvector.md) | Postgres for relational, vector, and keyword search | Accepted | 2026-09-22 |
| [0008](0008-sqlalchemy-async-alembic.md) | SQLAlchemy 2.x async with Alembic | Accepted | 2026-09-22 |
| [0009](0009-pydantic-settings-and-secrets.md) | Typed settings, env-only secrets | Accepted | 2026-09-22 |
| [0010](0010-supertokens-auth.md) | SuperTokens for authentication | Accepted | 2026-09-22 |
| [0011](0011-httponly-cookie-sessions.md) | httpOnly, same-origin cookie sessions | Accepted | 2026-09-22 |
| [0012](0012-sse-ai-sdk-streaming-protocol.md) | SSE streaming in the AI SDK v1 format | Accepted | 2026-09-22 |
| [0013](0013-testing-strategy.md) | Testing strategy | Accepted | 2026-09-22 |
| [0014](0014-vue3-vite-spa.md) | Vue 3 + Vite SPA | Accepted | 2026-09-22 |
| [0015](0015-primevue-tailwind-design-system.md) | PrimeVue 4 + Tailwind v4 design system | Accepted | 2026-09-22 |
| [0016](0016-caddy-single-origin.md) | Caddy as the single origin | Accepted | 2026-09-22 |
| [0017](0017-docker-compose-dev-deps.md) | Compose for dev dependencies only | Accepted | 2026-09-22 |
| [0018](0018-openrouter-llm-provider.md) | OpenRouter as the LLM provider | Accepted | 2026-09-22 |
| [0019](0019-llm-credentials-global-key-first.md) | Shared LLM key first, BYOK later | Accepted | 2026-09-22 |
| [0020](0020-redis-rate-limiting-middleware.md) | Redis-backed rate limiting middleware | Accepted | 2026-09-22 |
| [0021](0021-llm-provider-test-doubles.md) | LLM provider tests inject the SDK client | Accepted | 2026-09-22 |
| [0022](0022-streaming-endpoint-owns-history.md) | The streaming endpoint owns conversation history | Accepted | 2026-09-22 |
| [0023](0023-e2e-mock-provider.md) | Chat end-to-end tests run against a mock provider | Accepted | 2026-09-22 |
