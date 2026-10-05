# ADR-0037: A temporary conversation is not persisted until it is saved

- **Status:** Accepted
- **Date:** 2026-10-06
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

An incognito conversation lives only in the browser until the user saves it; only
then does it become an ordinary, stored conversation.

## Context

Users sometimes want a conversation that leaves no trace by default. If a
temporary conversation were stored server-side but merely hidden, its existence
would still depend on a retention promise rather than the absence of data.

## Decision

A temporary conversation is kept out of history and is not stored on the server
until the user saves it. Saving converts it into an ordinary conversation,
including its attachments. Unsaved, it cannot be reopened after the user leaves
it.

## Consequences

- **Easier:** a strong privacy default that does not rely on a deletion job.
- **Harder:** the client holds conversation state until save; "save" must carry
  both messages and attachments in one step.
- **We now live with:** temporary conversations that cannot be resumed by the
  server until saved.

## Alternatives considered

- **Stored but hidden** — simpler client, but the data exists server-side.
- **Stored with a short TTL** — a middle ground, still a retention promise.
