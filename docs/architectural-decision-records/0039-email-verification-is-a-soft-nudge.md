# ADR-0039: Email verification is a soft nudge with a reduced allowance

- **Status:** Accepted
- **Date:** 2026-10-06
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Verification never blocks sign-in; an unverified account gets half the chat
allowance and no uploads, and is nudged to verify.

## Context

Requiring verification before first use adds friction to the very first
impression. Ignoring verification entirely invites throwaway accounts. A middle
path keeps the product usable while giving verification a real incentive.

## Decision

An unverified account has half the normal chat allowance and no uploads or
retrieval. A verification email is sent shortly after sign-up, and a nudge is
shown when the reduced allowance is reached. Verification never blocks sign-in or
reading.

## Consequences

- **Easier:** first use stays frictionless; verification is encouraged, not
  forced.
- **Harder:** two allowance levels to reason about; a nudge that must not be
  nagging.
- **We now live with:** an allowance split between verified and unverified
  accounts.

## Alternatives considered

- **Hard gate** — strongest incentive, worst first impression.
- **No incentive** — simplest, invites disposable accounts.
- **Cap only uploads** — narrower, but leaves chat entirely unmetered for abuse.
