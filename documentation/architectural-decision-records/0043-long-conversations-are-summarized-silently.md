# ADR-0043: Long conversations are summarized silently

- **Status:** Accepted
- **Date:** 2026-10-06
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

As a conversation approaches the model's context limit, older turns are rolled
into a running summary; the user is not shown that this happened.

## Context

A conversation can grow beyond what the model can accept in one request. The
options are to drop old turns (losing continuity), refuse to continue, or
compress. Compression must preserve enough context that a follow-up still works,
without exposing an implementation detail to the user.

## Decision

Older turns are summarized into a running summary as the context limit nears.
The summary feeds the model but is not surfaced in the interface. The
conversation's stored history is not modified or shortened.

## Consequences

- **Easier:** conversations can continue indefinitely with bounded request size.
- **Harder:** a summarization step in the request path and a threshold to tune.
- **We now live with:** a small risk that a summarized detail is lost from
  context; stored history remains the source of truth.

## Alternatives considered

- **Keep full history** — eventually exceeds the model's window.
- **Trim oldest turns** — simple, but silently loses continuity.
- **Visible summary** — transparent, but adds interface noise.
