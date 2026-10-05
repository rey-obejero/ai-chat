# ADR-0021: LLM provider tests inject the SDK client

- **Status:** Accepted
- **Date:** 2026-09-22
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

The OpenRouter adapter is tested by injecting a fake OpenAI client, not by
intercepting its HTTP with respx.

## Context

ADR-0013 chose respx to fake provider HTTP. While implementing ADR-0018, the
OpenAI Python SDK resolved to a major version that speaks `httpx2` rather than
`httpx`. `respx` patches `httpx`, so it cannot intercept the SDK's requests at
all. Pinning the SDK to an older major purely to keep a test tool working would
trade a real dependency decision for a testing convenience.

## Decision

- `OpenAIChatProvider` takes an `AsyncOpenAI` client rather than constructing
  one, which makes the dependency injectable.
- Tests pass a fake client whose `chat.completions.create` records its arguments
  and returns a canned async stream of events.
- `build_chat_provider` is tested separately for configuration and the missing-key
  path; neither test touches HTTP.
- respx remains available for faking plain `httpx` calls elsewhere.

## Consequences

- **Easier:** adapter tests are fast and independent of the SDK's transport; the
  payload the adapter builds is asserted directly.
- **Harder:** the fake must mirror the SDK's event shape, so a breaking change in
  that shape is not caught by these tests.
- **We now live with:** two HTTP stacks in the back-end (`httpx` for tests and
  `httpx2` pulled in by the SDK), which is the SDK's choice rather than ours.

## Alternatives considered

- **Pin `openai` below the `httpx2` major** — keeps respx usable but freezes the
  SDK for the sake of a test tool.
- **Patch respx or the SDK's transport** — brittle and coupled to internals.
- **Test against the live provider** — costs money, needs a key, and is flaky.
