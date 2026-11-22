import type { RouteRecordRaw } from 'vue-router'

/**
 * The signed-in surface (ADR-0027). The grouping route carries no component and
 * one `requiresAuth`, which Vue Router merges into every child — including
 * routes added later. Its root redirects to the conversation list, so `/app`
 * is a usable address rather than an empty match.
 */
export const appRoutes: RouteRecordRaw[] = [
  {
    path: '/app',
    redirect: { name: 'conversations' },
    meta: { requiresAuth: true },
    children: [
      {
        path: 'conversations/:id?',
        name: 'conversations',
        component: () => import('@/features/conversations/views/ConversationsView.vue'),
      },
      // Reserved for the settings surface once it becomes a page. It is a
      // dialog opened from the application header today, so there is nothing to
      // route to yet.
    ],
  },
]
