# ADR-0015: PrimeVue 4 + Tailwind v4, themed from DESIGN.md

- **Status:** Accepted
- **Date:** 2026-09-22
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

UI primitives come from PrimeVue 4 and layout/styling from Tailwind v4, with
`DESIGN.md` as the binding visual contract and one theme preset mapping it.

## Context

The UI needs accessible, well-behaved components — menus, listboxes, dialogs,
avatars — that are time-consuming and error-prone to hand-roll, plus a strict,
near-monochrome visual language defined in `DESIGN.md`. Two styling systems in
one app risk drifting apart, so the theme needs a single translation point.

## Decision

- PrimeVue 4 in styled mode, configured through a custom preset.
- Tailwind CSS v4 with tokens declared in `src/assets/main.css` via
  `@theme`; no `tailwind.config.js`, and the Vite plugin is
  `@tailwindcss/vite`.
- The PrimeVue preset in `src/app/theme.ts` is the single place where
  `DESIGN.md` tokens are mapped onto components.
- `DESIGN.md` is binding for all UI work: no colors, fonts, spacing, or radii
  outside its tokens.
- Do not restyle PrimeVue with raw CSS overrides; extend the preset instead.
- Do not hand-roll a component that PrimeVue already provides.

## Consequences

- **Easier:** accessible components out of the box; a documented token set; UI
  review has an objective reference.
- **Harder:** two theming systems must be kept aligned — the Tailwind `@theme`
  tokens and the PrimeVue preset.
- **We now live with:** a component library's API to learn, and a preset file
  that becomes the first place to look when a component looks wrong.

## Alternatives considered

- **Hand-rolled components** — slow and an accessibility risk.
- **Another UI kit (Vuetify, Element Plus)** — heavier opinionation and less
  control over the monochrome aesthetic.
- **Tailwind only** — no accessible interactive primitives.
