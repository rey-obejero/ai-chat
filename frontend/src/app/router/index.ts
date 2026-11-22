import { createRouter, createWebHistory } from 'vue-router'

import { useSessionStore } from '@/features/auth/stores/session'
import { safeRedirect } from '@/lib/redirect'

import { appRoutes } from '../routes/app'
import { authRoutes } from '../routes/auth'
import { errorRoutes } from '../routes/errors'

/**
 * The public URL space is partitioned into two namespaces (ADR-0027):
 * `/auth/*` for the signed-out surface and `/app/*` for the
 * authenticated one. Route *names* are the stable contract — prefer navigating
 * by name so the next path change is a one-line edit in a route module rather
 * than a grep.
 *
 * The route table itself is split by surface under `app/routes/`; this module
 * only composes it and owns the navigation guard.
 *
 * `/api/auth` is deliberately outside this scheme: it is SuperTokens' own API
 * path, fixed by `api_base_path`, and the OAuth provider consoles point at it.
 */
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: { name: 'conversations' } },
    ...authRoutes,
    ...appRoutes,
    ...errorRoutes,
  ],
})

router.beforeEach(async (to) => {
  const session = useSessionStore()
  if (!session.ready) {
    await session.refresh()
  }

  if (to.meta.requiresAuth && !session.isAuthenticated) {
    // A failed session check is not the same as "signed out": signing in cannot
    // fix an unreachable API, so send the user to the retry screen instead.
    if (session.unavailable) {
      return { name: 'unavailable' }
    }

    // `redirectTo` is a public contract, so the consumer validates it rather
    // than trusting it — see `safeRedirect`.
    return { name: 'sign-in', query: { redirectTo: to.fullPath } }
  }

  if ((to.name === 'sign-in' || to.name === 'sign-up') && session.isAuthenticated) {
    // Honour the destination here too. Dropping it sent an already-signed-in
    // user to the conversation list even when the link they followed named a
    // specific conversation.
    return safeRedirect(to.query.redirectTo, { name: 'conversations' })
  }

  return true
})

router.afterEach((to) => {
  const page = to.meta.title as string | undefined
  document.title = page ? `${page} | AI Chat` : 'AI Chat'
})

export { router }
