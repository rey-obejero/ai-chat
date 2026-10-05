# ADR-0023: Chat end-to-end tests run against a mock provider

- **Status:** Accepted
- **Date:** 2026-09-22
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

The e2e suite starts a deterministic OpenAI-compatible server and points the API
at it with `LLM_BASE_URL`, so the browser → API → provider path is exercised
without a key, a network call, or a real model.

## Context

The chat flow is only worth testing end to end if a reply actually streams.
Mocking the API in the browser would skip the part most likely to break — the
SSE wiring between the emitter (ADR-0012) and the client transport (ADR-0022).
ADR-0013 chose respx for provider HTTP in back-end tests, but that lives outside
the browser and cannot cover the client.

Calling a real provider in e2e would need a secret in CI, cost money per run,
and return text that is not deterministic enough to assert on.

## Decision

- `e2e/support/mock-llm-server.mjs` serves `POST /v1/chat/completions` as SSE in
  the OpenAI chunk format. It echoes the newest user turn and streams the reply
  in small pieces, so a spec can assert both that the message reached the
  provider and that streaming (not one chunk) is what arrived.
- Playwright's `webServer` starts it, and starts the API with `LLM_BASE_URL`
  pointing at it plus a throwaway `LLM_API_KEY`. The provider port (ADR-0018) is
  what makes this a configuration change rather than a code change.
- Specs sign up a fresh account, create a conversation, send a message, and
  assert the streamed reply plus its persistence across a reload.

## Consequences

- **Easier:** the whole path is covered deterministically and offline; CI needs
  no provider secret; a failure points at our wiring, not a model's mood.
- **Harder:** the mock must stay faithful to the OpenAI streaming shape, so a
  provider-side format change is not caught here.
- **We now live with:** `reuseExistingServer` means a developer who already has
  `just back-end` running will have e2e reuse that instance, which lacks the mock
  configuration. Stop dev servers before `just test-e2e`, or the chat specs will
  see 503s.

## Alternatives considered

- **Mock the chat endpoint in the browser** — skips the SSE and persistence path,
  which is the whole point.
- **Call a real provider** — needs a secret, costs money, and is not
  deterministic.
- **Record and replay real provider traffic** — brittle against model and format
  changes, and still needs a key to record.
