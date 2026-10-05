# ADR-0041: Internationalization covers the interface only

- **Status:** Accepted
- **Date:** 2026-10-06
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

The interface is translated, launching in English and Chinese (Simplified); the
assistant's reply language is not steered by the setting.

## Context

The product should not require English, but the interface holds an additional
constraint: the typography contract uses a Latin-only font with tight tracking,
and Chinese needs a CJK fallback and per-character line-breaking. Stepping into
"reply language" would also mean prompt manipulation, which is a separate
concern.

## Decision

i18n covers the interface only. Launch languages are English and Chinese
(Simplified). The chosen language is remembered, and a missing translation falls
back to English. Assistant replies are not steered by the setting.

## Consequences

- **Easier:** a bounded translation surface and no prompt coupling.
- **Harder:** the design contract must add a CJK font fallback and revisit
  line-breaking and letter-spacing.
- **We now live with:** a translation catalogue that must stay complete.

## Alternatives considered

- **Steer reply language too** — more control, couples UI language to prompting.
- **Defer i18n entirely** — smallest scope, but closes out non-English users.
