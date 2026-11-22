# ADR-0045: Display names default to the email local part and are filtered

- **Status:** Accepted
- **Date:** 2026-10-06
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

On first sign-in the user is asked how to be addressed; skipping keeps the email
local part verbatim as the name.

## Context

The product addresses the user by name, but requiring a name at sign-up adds
friction. A sensible default avoids a nameless account without asking for
anything, while a short prompt lets users who care set their own.

## Decision

A first-run, skippable prompt sets the display name. The default is the local
part of the email address, unchanged (for example `s82jdna` from
`s82jdna@example.com`). The name is 1–50 characters, is filtered for profanity,
is never blank, and is editable from settings.

## Consequences

- **Easier:** a personal greeting with no forced input; a name that is always
  present.
- **Harder:** a profanity filter and a default that can look like an identifier
  for machine-generated addresses.
- **We now live with:** a derived default the user may never change.

## Alternatives considered

- **Required prompt** — a name always chosen, but adds a gate to first use.
- **Provider name when available** — nicer for social sign-in, unavailable for
  password accounts.
- **Generic "there"** — no filter needed, but impersonal.
