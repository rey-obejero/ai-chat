import { createMemoryHistory, createRouter } from 'vue-router'
import { describe, expect, it } from 'vitest'

import { appRoutes } from '@/app/routes/app'
import { authRoutes } from '@/app/routes/auth'
import { errorRoutes } from '@/app/routes/errors'

/** Every signed-out screen, by route name (names are the contract). */
const PUBLIC_ROUTE_NAMES = [
  'sign-in',
  'sign-up',
  'auth-callback',
  'forgot-password',
  'reset-password',
  'verify-email',
] as const

const routesByName = new Map(
  [...authRoutes, ...errorRoutes].map((route) => [route.name, route] as const),
)

describe('app route table', () => {
  it.each(PUBLIC_ROUTE_NAMES)('declares %s public explicitly', (name) => {
    const route = routesByName.get(name)

    expect(route).toBeDefined()
    expect(route?.meta?.requiresAuth).toBe(false)
  })

  it('serves the catch-all 404 without a session', () => {
    const notFound = routesByName.get('not-found')

    expect(notFound?.path).toBe('/:pathMatch(.*)*')
    expect(notFound?.meta?.requiresAuth).toBe(false)
  })

  it('serves the retry screen without a session', () => {
    const unavailable = routesByName.get('unavailable')

    expect(unavailable?.path).toBe('/unavailable')
    expect(unavailable?.meta?.requiresAuth).toBe(false)
  })

  it('protects every route under /app, including through inheritance', () => {
    const app = appRoutes.find((route) => route.path === '/app')

    expect(app?.meta?.requiresAuth).toBe(true)

    // Merged from the grouping route at resolve time, not just declared on it.
    const router = createRouter({ history: createMemoryHistory(), routes: appRoutes })
    expect(router.resolve('/app/conversations').meta.requiresAuth).toBe(true)
    expect(router.resolve('/app/conversations/abc').meta.requiresAuth).toBe(true)
  })

  it('redirects /app itself to the conversations route', () => {
    const app = appRoutes.find((route) => route.path === '/app')

    expect(app && 'redirect' in app ? app.redirect : undefined).toEqual({
      name: 'conversations',
    })
  })
})
