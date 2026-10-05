# ADR-0022: The streaming endpoint owns conversation history

- **Status:** Accepted
- **Date:** 2026-09-22
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

`POST /conversations/{id}/messages` takes only the new user text; the server
loads the history, streams the reply, and persists both turns.

## Context

The AI SDK's `useChat` conventionally posts the whole message array every turn
and keeps conversation state in the browser. That conflicts with this product:
conversations are persisted server-side and listed in the sidebar, so a client
array becomes a second, competing source of truth. Accepting history from the
client would also let it replay or fabricate prior turns.

## Decision

- The request body is `{"content": "<the new user message>"}`. History is never
  accepted from the client.
- The server persists the user turn, loads the ordered history, builds the
  provider prompt, streams the assistant reply as SSE (ADR-0012), and persists
  the assistant turn once the stream completes.
- Invalid input is rejected before streaming begins, so the client receives a
  normal RFC 9457 problem response. A failure after the first byte is reported
  as an `error` part inside the stream, because the status is already committed.
- The assistant turn is written from a second, short-lived session: FastAPI
  closes request-scoped dependencies before the response body is streamed, so
  the request's own session is no longer usable by then.
- The client uses `useChat` with a custom transport that sends only the new text.

## Consequences

- **Easier:** one source of truth for history; the server controls the prompt
  and its token budget; a client cannot inject prior turns.
- **Harder:** the client must customize the SDK transport instead of using the
  default `{messages}` contract.
- **We now live with:** a second session opened per reply; an endpoint that must
  distinguish pre-stream errors (problem+json) from mid-stream errors (an
  `error` part); and a client that must copy `useChat`'s message array before
  binding it, because the SDK mutates the array in place and Vue will otherwise
  skip the child update when only its contents changed.

## Alternatives considered

- **Accept the client's message array (the SDK default)** — a competing source
  of truth, and a way to fabricate history.
- **Persist the assistant turn with the request-scoped session** — the session
  is closed before the body streams; this fails at runtime.
- **Buffer the reply and return one JSON object** — loses the token-by-token
  streaming that is the point of the feature.
