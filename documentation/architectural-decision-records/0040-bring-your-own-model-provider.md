# ADR-0040: A user may bring their own compatible model provider

- **Status:** Accepted
- **Date:** 2026-10-06
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

In addition to the server-provided model, a user may connect their own
OpenAI-compatible provider; the key is stored encrypted server-side and never
returned to the browser.

## Context

ADR-0019 chose a shared server key first, with BYOK "later". Power users may
prefer their own provider and billing. A user-supplied key is a credential held
on the server, so it must never leak back to the client or into logs, and it must
not be usable across accounts.

## Decision

A user may select **Auto** (the server-provided model) or **BYOK**: a compatible
third-party provider configured with a base URL, key, and model. The key is
stored server-side, encrypted, is used only for its owner's requests, is never
shown back in full or logged, and is never exposed when switching providers.
BYOK usage is not counted against the server's token quota but remains
rate-limited.

## Consequences

- **Easier:** users can choose their provider and cover their own cost.
- **Harder:** secure at-rest key storage and per-request provider selection.
- **We now live with:** quota accounting that treats BYOK and Auto differently.

## Alternatives considered

- **Auto only** — ADR-0019's earlier position; no BYOK.
- **Key held in the browser** — no server secret, but sent on every request.
- **Session-only key** — safer, but re-entered each session.
