# AGENTS.md — front-end

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
front-end/src/
├── main.ts                 # bootstraps SuperTokens + providers + router
├── App.vue
├── app/                    # cross-cutting app wiring (not a feature)
│   ├── providers.ts        # Pinia + PrimeVue (theme preset)
│   ├── theme.ts            # PrimeVue preset mapped from DESIGN.md
│   └── router/index.ts     # routes + auth guard
├── features/
│   ├── auth/               # index.ts is the public API
│   │   ├── api.ts  stores/  components/  views/
│   └── chat/               # index.ts is the public API
│       ├── stores/  components/  views/
├── components/             # global shared components
├── stores/                 # global stores (feature stores stay in features/)
└── lib/api.ts              # fetch wrapper for /api/v1 (RFC 9457 aware)
tests/<feature>/unit/
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

From the repo root, prefer `just front-end` / `just test-front-end` / `just lint`.

## Design system (DESIGN.md — obey it)

- **Colors:** primary/secondary/success/warning/danger/surface/text/neutral.
  Tailwind tokens are declared in `src/assets/main.css` under `@theme`.
- **Typography:** display Inter, body Open Sans, mono Inconsolata; `h1` is 3rem.
  Use the `.label-caps` helper for the mono uppercase small caps.
- **Spacing scale:** 4/8/12/16/24/32. **Radius:** sm 4px, md 8px.
- Do not introduce colors, fonts, or spacing outside these tokens.

## Architecture rules

- A feature is a vertical slice: its internals stay inside `features/<x>/`;
  everything is exposed through `features/<x>/index.ts`. Other features and
  `app/` import only from that public API.
- `app/` is the composition root (providers, router); it holds no business logic.
- `lib/` holds framework-agnostic helpers. `components/` and `stores/` are for
  truly global pieces only.

## Tailwind v4

- No `tailwind.config.js`. Tokens live in `src/assets/main.css` via
  `@theme { --color-… }`, and the Vite plugin is `@tailwindcss/vite`.
- Prefer utility classes; compose variants in the template.

## Do

- Use `<script setup lang="ts">` and type props/emits.
- Talk to the API only through `src/lib/api.ts` (`/api/v1`, same-origin).
- Guard protected routes in `app/router/index.ts` via the session store.
- Keep auth state in Pinia, never in `localStorage`/`sessionStorage`.

## Don't

- Don't store tokens or session data in web storage — SuperTokens uses
  httpOnly cookies (same-origin, no BFF).
- Don't import another feature's internals (respect `index.ts`).
- Don't add a second CSS framework or hand-roll a component PrimeVue covers.
- Don't restyle PrimeVue with raw CSS overrides; extend the preset in
  `src/app/theme.ts`.
