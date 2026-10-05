# ADR-0042: Dark mode is per-account and extends the design contract

- **Status:** Accepted
- **Date:** 2026-10-06
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Light, dark, or follow-system is remembered per account and synced across
devices, and the design contract gains a dark token set.

## Context

The design system (`DESIGN.md`) is light-only and binding, and the component
theme defines a single light colour scheme. A dark mode is not just a toggle: it
needs a parallel set of colour values that meet contrast, applied consistently
across every component.

## Decision

The user chooses light, dark, or follow-system. The choice is stored with the
account and applied on any device the user signs in from. The design contract
gains matching dark tokens, and the component theme gains a dark colour scheme.
The wrong theme must never flash while the interface loads.

## Consequences

- **Easier:** a consistent theme across a user's devices.
- **Harder:** every colour token needs a dark counterpart that meets contrast;
  the theme must resolve before first paint.
- **We now live with:** a design contract that must be maintained in both themes.

## Alternatives considered

- **Per-device only** — simpler, but the choice does not follow the user.
- **System-only** — no stored preference, less control.
