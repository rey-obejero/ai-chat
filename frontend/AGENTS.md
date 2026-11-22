# AGENTS.md — frontend

Vue 3 + Vite SPA for AI Chat. Root guide: `../AGENTS.md`.
The UI contract is **`../DESIGN.md`** — it is binding for all UI work.

## Stack (detailed)

- **Framework:** Vue 3 (`<script setup lang="ts">`) + Vite SPA (not Nuxt)
- **UI:** PrimeVue 4 (custom preset, styled mode) + Tailwind CSS **v4**
- **State:** Pinia · **Routing:** vue-router 4
- **Auth:** `supertokens-web-js` (Session + EmailPassword + ThirdParty)
- **Types:** TypeScript strict (`verbatimModuleSyntax`)
- **Tests:** Vitest + Vue Test Utils (jsdom)

## Layout

```
frontend/src/
├── main.ts                 # bootstraps SuperTokens + providers + router
├── App.vue
├── app/                    # cross-cutting app wiring (not a feature)
│   ├── providers.ts        # Pinia + PrimeVue (theme preset)
│   ├── routes/             # thin route modules: auth, app, errors
│   ├── theme.ts            # PrimeVue preset mapped from DESIGN.md
│   └── router/index.ts     # composes the route modules + auth guard
├── features/
│   ├── auth/               # api.ts  stores/  components/  views/
│   ├── conversations/      # api.ts  messages.ts  stores/  components/  views/
│   ├── settings/           # the settings modal (Usage + Provider)
│   └── usage/              # token-usage store + panel (ADR-0024)
├── components/             # global shared components
├── stores/                 # global stores (feature stores stay in features/)
└── lib/api.ts              # fetch wrapper for /api/v1 (RFC 9457 aware)
tests/<feature>/unit/  tests/app/router/
```

## Commands

```sh
pnpm dev            # Vite dev server on :5173 (proxies /api → :8000)
pnpm build          # vue-tsc --noEmit && vite build
pnpm test           # Vitest
pnpm typecheck      # vue-tsc --noEmit
pnpm lint           # eslint . --fix
pnpm format         # prettier --write src
```

From the repo root, prefer `just development` — native, with the SPA on Vite and
the datastores in Compose (ADR-0046) — and `just test-frontend` / `just lint`
for the rest. `just frontend` runs Vite alone.

## Design system

The contract is [`DESIGN.md`](../DESIGN.md) — binding for colors, typography,
spacing, radii, and components. Read it before any UI work; don't restate its
tokens here, and don't introduce values outside them. Implementations of the
tokens are noted under "Tailwind v4" and "Don't" below.

## Architecture rules

- A feature is a vertical slice: its internals stay inside `features/<x>/`.
  There is no barrel — routes, other features, and tests import the concrete
  file they need. A `features/<x>/index.ts` re-export is retired, not a
  convention.
- Route records live in thin modules under `app/routes/` (`auth`, `app`,
  `errors`); each route lazy-loads its view file directly. `app/router/index.ts`
  only composes those arrays and owns the guard.
- Public URL segments are `/auth` and `/app` (ADR-0027). Route **names** are the
  contract — navigate by name.
- `app/` is the composition root (providers, router); it holds no business logic.
- `lib/` holds framework-agnostic helpers. `components/` and `stores/` are for
  truly global pieces only.

## Tailwind v4

- No `tailwind.config.js`. Tokens live in `src/assets/main.css` via
  `@theme { --color-… }`, and the Vite plugin is `@tailwindcss/vite`.
- Prefer utility classes; compose variants in the template.

## Tailwind and PrimeVue layering

PrimeVue ships unlayered CSS, which outranks `@layer utilities` regardless of
specificity. Any utility that must beat a PrimeVue component style needs an
important marker (`!size-8`, `!text-body-sm`) — a bare `text-sm` on a
`.p-button`, for example, silently loses to PrimeVue's 16px and the label
renders at the wrong size. Prefer extending the preset in `src/app/theme.ts`;
use `!` only for genuine utility overrides on a PrimeVue element. Do not rely
on `group-*` variants anywhere: they are inert in this build. Use scoped
`:hover` / `:focus-within` rules instead.

## Do

- Use `<script setup lang="ts">` and type props/emits.
- Talk to the API only through `src/lib/api.ts` (`/api/v1`, same-origin).
- Guard protected routes in `app/router/index.ts` via the session store.
- Keep auth state in Pinia. Never put tokens or session data in
  `localStorage`/`sessionStorage`; a non-secret value that must survive a
  full-page navigation (the post-sign-in destination) may use `sessionStorage`,
  scoped to the tab and cleared when read.

## Don't

- Don't store tokens or session data in web storage — SuperTokens uses
  httpOnly cookies (same-origin, no BFF).
- Don't add a `features/<x>/index.ts` barrel — import the concrete file.
- Don't add a second CSS framework or hand-roll a component PrimeVue covers.
- Don't restyle PrimeVue with raw CSS overrides; extend the preset in
  `src/app/theme.ts`.
