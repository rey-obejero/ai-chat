import { createRouter, createWebHistory } from 'vue-router'

import { useSessionStore } from '@/features/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/conversations' },
    {
      path: '/sign-in',
      name: 'sign-in',
      component: () => import('@/features/auth').then((m) => m.SignInView),
    },
    {
      path: '/sign-up',
      name: 'sign-up',
      component: () => import('@/features/auth').then((m) => m.SignupView),
    },
    {
      path: '/auth/callback',
      name: 'auth-callback',
      component: () => import('@/features/auth').then((m) => m.AuthCallbackView),
    },
    {
      path: '/conversations',
      name: 'conversations',
      component: () => import('@/features/conversations').then((m) => m.ConversationsView),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach(async (to) => {
  const session = useSessionStore()
  if (!session.ready) {
    await session.refresh()
  }

  if (to.meta.requiresAuth && !session.isAuthenticated) {
    return { name: 'sign-in', query: { redirect: to.fullPath } }
  }

  if ((to.name === 'sign-in' || to.name === 'sign-up') && session.isAuthenticated) {
    return { name: 'conversations' }
  }

  return true
})

export { router }
