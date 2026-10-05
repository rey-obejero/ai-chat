# ADR-0014: The front-end is a Vue 3 + Vite SPA

- **Status:** Accepted
- **Date:** 2026-09-22
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

The client is a single-page application built with Vue 3 and Vite, served as
static files.

## Context

The product is an authenticated chat application behind a login. There is no
public content that needs indexing by search engines, and the deployment target
serves static files behind a reverse proxy. Server rendering would add a runtime
and a second rendering path for no user-visible benefit.

## Decision

- Vue 3 with `<script setup lang="ts">` and Vite.
- `vue-router` for routing and auth guards; Pinia for state.
- TypeScript strict, including `verbatimModuleSyntax`.
- The build output is static and served by Caddy; `/api` is proxied in
  development by Vite and in production by the reverse proxy.

## Consequences

- **Easier:** a trivial deploy (static files), instant navigation after load,
  and one rendering model to reason about.
- **Harder:** no server rendering, so initial load and link previews depend on
  the client; route protection is a UX guard, never a security boundary.
- **We now live with:** the API must be the authority on authorization, because
  the client can be bypassed.

## Alternatives considered

- **Nuxt** — SSR and file-based conventions we don't need.
- **React / Svelte** — viable; Vue with PrimeVue fit the component needs and
  prior familiarity.
- **Multi-page server-rendered app** — worse interactivity for a chat UI.
