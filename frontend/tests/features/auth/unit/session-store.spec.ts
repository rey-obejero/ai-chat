import { createPinia, setActivePinia } from 'pinia'
import Session from 'supertokens-web-js/recipe/session'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getMe, type User } from '@/features/auth/api'
import { useSessionStore } from '@/features/auth/stores/session'
import { ApiError } from '@/lib/api'

vi.mock('supertokens-web-js/recipe/session', () => ({
  default: { doesSessionExist: vi.fn(), signOut: vi.fn() },
}))

vi.mock('@/features/auth/api', () => ({ getMe: vi.fn(), updateMe: vi.fn() }))

const sessionExists = vi.mocked(Session.doesSessionExist)
const me = vi.mocked(getMe)

const USER = { id: 'user-1', email: 'person@example.com' } as User

function apiError(status: number): ApiError {
  return new ApiError({ type: 'about:blank', title: 'Failed', status })
}

describe('session store refresh', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    sessionExists.mockReset()
    me.mockReset()
  })

  it('treats a missing session as signed out, not unavailable', async () => {
    sessionExists.mockResolvedValue(false)
    const session = useSessionStore()

    await session.refresh()

    expect(session.user).toBeNull()
    expect(session.isAuthenticated).toBe(false)
    expect(session.unavailable).toBe(false)
    expect(session.ready).toBe(true)
    expect(me).not.toHaveBeenCalled()
  })

  it('reads the account when the session exists', async () => {
    sessionExists.mockResolvedValue(true)
    me.mockResolvedValue(USER)
    const session = useSessionStore()

    await session.refresh()

    expect(session.user).toEqual(USER)
    expect(session.isAuthenticated).toBe(true)
    expect(session.unavailable).toBe(false)
  })

  it('treats a 401 from the account endpoint as signed out', async () => {
    sessionExists.mockResolvedValue(true)
    me.mockRejectedValue(apiError(401))
    const session = useSessionStore()

    await session.refresh()

    expect(session.user).toBeNull()
    expect(session.unavailable).toBe(false)
    expect(session.ready).toBe(true)
  })

  it('marks a server failure as unavailable rather than signed out', async () => {
    sessionExists.mockResolvedValue(true)
    me.mockRejectedValue(apiError(503))
    const session = useSessionStore()

    await session.refresh()

    expect(session.user).toBeNull()
    expect(session.unavailable).toBe(true)
    expect(session.ready).toBe(true)
  })

  it('marks a network failure on the session check as unavailable', async () => {
    sessionExists.mockRejectedValue(new TypeError('Failed to fetch'))
    const session = useSessionStore()

    await session.refresh()

    expect(session.user).toBeNull()
    expect(session.unavailable).toBe(true)
    expect(session.ready).toBe(true)
  })

  it('clears unavailable when a later refresh succeeds', async () => {
    sessionExists.mockResolvedValue(true)
    me.mockRejectedValueOnce(apiError(502)).mockResolvedValueOnce(USER)
    const session = useSessionStore()

    await session.refresh()
    expect(session.unavailable).toBe(true)

    await session.refresh()
    expect(session.user).toEqual(USER)
    expect(session.unavailable).toBe(false)
  })
})
