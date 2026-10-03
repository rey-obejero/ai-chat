import { createRouter, createWebHistory } from 'vue-router'

import { useSessionStore } from '@/features/auth'
import { safeRedirect } from '@/lib/redirect'

/**
 * The public URL space is partitioned into two namespaces (ADR-0027):
 * `/authentication/*` for the signed-out surface and `/application/*` for the
 * authenticated one. Route *names* are the stable contract — prefer navigating
 * by name so the next path change is a one-line edit here rather than a grep.
 *
 * `/api/auth` is deliberately outside this scheme: it is SuperTokens' own API
 * path, fixed by `api_base_path`, and the OAuth provider consoles point at it.
 */
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: { name: 'conversations' } },
    {
      path: '/authentication/sign-in',
      name: 'sign-in',
      component: () => import('@/features/auth').then((m) => m.SignInView),
      meta: { title: 'Sign In' },
    },
    {
      path: '/authentication/sign-up',
      name: 'sign-up',
      component: () => import('@/features/auth').then((m) => m.SignupView),
      meta: { title: 'Sign Up' },
    },
    {
      // SuperTokens' backend handles the provider callback, then forwards the
      // browser here. The provider never sees this route.
      path: '/authentication/callback',
      name: 'auth-callback',
      component: () => import('@/features/auth').then((m) => m.AuthCallbackView),
      meta: { title: 'Sign In' },
    },
    {
      // No component: a grouping route. `meta` is merged into every child, so
      // one `requiresAuth` covers the whole authenticated surface, including
      // routes added later.
      path: '/application',
      meta: { requiresAuth: true },
      children: [
        {
          path: 'conversations/:id?',
          name: 'conversations',
          component: () => import('@/features/conversations').then((m) => m.ConversationsView),
        },
        // Reserved for the settings surface once it becomes a page. It is a
        // dialog opened from the application header today, so there is nothing
        // to route to yet.
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/features/errors').then((m) => m.NotFoundView),
      meta: { title: 'Not Found' },
    },
  ],
})

router.beforeEach(async (to) => {
  const session = useSessionStore()
  if (!session.ready) {
    await session.refresh()
  }

  if (to.meta.requiresAuth && !session.isAuthenticated) {
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
