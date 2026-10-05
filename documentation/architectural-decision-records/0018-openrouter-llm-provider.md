# ADR-0018: OpenRouter is the LLM provider

- **Status:** Accepted
- **Date:** 2026-09-22
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

One OpenRouter account serves both chat completions and embeddings through an
OpenAI-compatible API, reached from a provider port so the vendor stays
swappable.

## Context

The product needs chat completions now and embeddings when document retrieval
lands. Offering a demo means paying for inference, so cost control matters, and
the provider decision had been deferred to build time. Hard-wiring a vendor SDK
into the chat path would make a later switch expensive, and picking a
chat-only provider would force a second vendor for embeddings.

## Decision

- The back-end talks to OpenRouter at `https://openrouter.ai/api/v1` using the
  OpenAI Python SDK with a configurable base URL.
- The same base URL and key cover chat completions and embeddings; the
  embeddings endpoint is OpenAI-compatible and non-streaming.
- Settings: `llm_api_key`, `llm_base_url`, `llm_model`, an embedding model, plus
  a request timeout and output-token cap.
- Requests carry optional attribution headers (`HTTP-Referer`, `X-Title`) so
  usage is identifiable in the provider dashboard.
- Provider access sits behind a `ChatProvider` port in an `llm` feature slice,
  not a direct SDK call in the chat route.
- Tests fake the provider's HTTP with `respx` (see ADR-0013).

## Consequences

- **Easier:** one key and one endpoint for chat and retrieval; cheap models are
  available; switching vendors or pointing at a local model is a configuration
  change behind the port.
- **Harder:** a gateway sits in the request path, adding a latency hop and its
  own failure modes; model identifiers are OpenRouter-prefixed
  (for example `openai/...`, `google/...`).
- **We now live with:** the port as the only place that knows a vendor exists,
  and a default model chosen for cost rather than peak quality.

## Alternatives considered

- **OpenAI direct** — higher cost and a single vendor for both chat and
  embeddings.
- **Anthropic direct** — strong chat models, but a different wire format and no
  embeddings, so retrieval still needs a second provider.
- **Two vendors (chat + embeddings)** — two keys, two bills, two failure modes.
- **A self-hosted model** — avoids per-token cost but adds GPU operations that
  are out of scope for this project.
