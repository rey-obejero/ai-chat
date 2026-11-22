# ADR-0038: Password strength is length, entropy, and breach screening

- **Status:** Accepted
- **Date:** 2026-10-06
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

A password must be at least 8 characters, pass an entropy check, and not appear
in breached-password data.

## Context

The authentication service enforces only a basic password policy and has no
entropy scoring or breach list, so it cannot meet the product's account-safety
goal on its own. Composition rules ("one upper, one number") are widely
considered weak and are easy for users to game.

## Decision

A password is rejected, before the account is created, when it is shorter than 8
characters, when an entropy check judges it weak or common, or when it appears in
breached-password data. The breach check is performed server-side, on submit, in
a privacy-preserving way that does not send the password itself.

## Consequences

- **Easier:** materially fewer weak or already-leaked passwords.
- **Harder:** a server-side validator beyond the auth service's built-in policy;
  a dependency on breached-password data.
- **We now live with:** an external check on the sign-up and reset paths that
  must degrade sensibly when unavailable.

## Alternatives considered

- **Length only** — misses leaked and common passwords.
- **Composition rules** — annoying and weakly correlated with strength.
- **Client-side only** — trivially bypassed.
