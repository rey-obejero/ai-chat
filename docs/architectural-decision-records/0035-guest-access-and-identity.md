# ADR-0035: Guests can chat, and their conversations are claimed at sign-up

- **Status:** Proposed
- **Date:** 2026-10-06
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

An unauthenticated visitor may hold a conversation, and signing up claims those
conversations into the new account.

## Context

Every stored conversation currently requires an owning account, so the sign-up
form is the first thing a visitor meets. The product wants to be tryable without
an account. Relaxing this raises three unanswered questions: who the owner of a
guest conversation is, how guest usage is limited, and how a guest's data is
retained. The identity mechanism itself (an anonymous session, a device id, or
no server persistence) is not yet decided.

## Decision

Guests may chat without an account. A guest sees only their own conversations;
guest usage is rate-limited and spend-capped; guest conversations are deleted
after 30 days; and signing up moves a guest's conversations into the new
account, orphaning none.

The identity mechanism is deliberately left open and will be settled in a
follow-up decision that supersedes or amends this one.

## Consequences

- **Easier:** a real first impression without a sign-up wall; a natural upgrade
  path from guest to account.
- **Harder:** conversations and quota must allow an owner that is not an
  account; a claim path must move rows without duplicating or stranding them.
- **We now live with:** a retention job for guest data, and a guest rate/quota
  policy separate from the per-user one.

## Alternatives considered

- **Anonymous cookie session** — persisted and claimable, but needs a session
  mechanism and server state.
- **Client-only until sign-in** — simplest and safest, but nothing survives a
  device change.
- **Device id** — no cookie, but fragile across devices and clears.
