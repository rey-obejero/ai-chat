import type { RouteRecordRaw } from 'vue-router'

/**
 * Fall-through routes: rendered without a session check, and therefore public.
 */
export const errorRoutes: RouteRecordRaw[] = [
  {
    // Reached when the session check failed rather than answered "signed out".
    // The guard sends protected routes here so the user can retry instead of
    // being told to sign in to a service that is not answering.
    path: '/unavailable',
    name: 'unavailable',
    component: () => import('@/features/errors/views/UnavailableView.vue'),
    meta: { title: 'Service Unavailable', requiresAuth: false },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/features/errors/views/NotFoundView.vue'),
    meta: { title: 'Not Found', requiresAuth: false },
  },
]
