# ADR-0012: Replies stream over SSE in the AI SDK v1 format

- **Status:** Accepted
- **Date:** 2026-09-22
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

The back-end emits server-sent events in the AI SDK v1 data-stream format from a
hand-rolled FastAPI module; the front-end consumes them with `@ai-sdk/vue`.

## Context

Model replies must appear token by token. The wire format is a real decision
because the client is a maintained library: if the server drifts from what the
client expects, streaming breaks in subtle ways and debugging means reading two
codebases.

## Decision

- Front-end: `@ai-sdk/vue`'s `useChat`.
- Back-end: a small hand-rolled emitter, currently `shared/streaming/ai_sdk.py`,
  speaking the AI SDK's **UI Message Stream** protocol, version 1 — SSE whose
  `data:` payloads are typed JSON parts, terminated by a literal `[DONE]`. The
  response pins the version with `x-vercel-ai-ui-message-stream: v1`.
- The parts used so far are `start`, `text-start`, `text-delta`, `text-end`,
  `finish`, and `error`. Source documents for citations and tool input/output
  follow the same typed-JSON shape. The agent loop runs server-side, so
  step-level events are unnecessary.
- The protocol is isolated in one module, and a fixture test guards against
  upstream spec drift.
- The Vercel beta Python port is explicitly not used.

## Consequences

- **Easier:** a maintained client handles parsing, message state, and rendering;
  the protocol lives in one file with a guard test.
- **Harder:** we own the emitter and the spec-drift test; the client library's
  major versions are a compatibility event.
- **We now live with:** the exact event shapes are a contract, and changing them
  is a coordinated front-end/back-end change.

## Alternatives considered

- **A hand-rolled SSE reader on the client** — more client code and a bespoke
  protocol to maintain.
- **The Vercel beta Python port** — effectively unmaintained for this use.
- **WebSockets** — bidirectional transport for a one-way stream; heavier.
- **Long polling** — no token-by-token rendering.
