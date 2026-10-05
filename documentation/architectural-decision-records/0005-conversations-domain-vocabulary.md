# ADR-0005: The domain says "conversation", never "chat"

- **Status:** Accepted
- **Date:** 2026-09-22
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Conversations are the entity and the feature; "chat" survives only as the
product's name.

## Context

The project began using "chat" for three different things: the product ("AI
Chat"), the act of chatting, and the stored entity. That ambiguity shows up in
URLs, table names, types, and module paths, and makes it unclear what any given
`chat` refers to.

## Decision

- Feature slices, tables, routes, schemas, and types use `conversation` /
  `conversations`.
- The API route is `/api/v1/conversations`; the back-end slice is
  `ai_chat.conversations`; the front-end feature is `features/conversations`.
- "AI Chat" remains the product's display name, and is the only sanctioned use
  of the word.
- Any pre-existing `chat`-named code, route, or type is a rename, not a synonym.

## Consequences

- **Easier:** one word per concept; searches for "chat" surface only branding.
- **Harder:** historical references and external notes that say "chat" must be
  translated mentally to "conversation".
- **We now live with:** a deliberate branding exception that has to be stated
  whenever it looks like a violation.

## Alternatives considered

- **Keep "chat" for the entity** — collides with the product name and stays
  ambiguous.
- **Use both interchangeably** — the worst of the options; guarantees drift.
