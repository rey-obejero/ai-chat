import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { formatTokens } from '@/features/usage/format'
import { useUsageStore } from '@/features/usage/stores/usage'

describe('formatTokens', () => {
  it('leaves small counts alone', () => {
    expect(formatTokens(0)).toBe('0')
    expect(formatTokens(999)).toBe('999')
  })

  it('compacts thousands', () => {
    expect(formatTokens(1000)).toBe('1k')
    expect(formatTokens(82_000)).toBe('82k')
    expect(formatTokens(1234)).toBe('1.2k')
    expect(formatTokens(99_980)).toBe('100k')
  })
})

describe('useUsageStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('loads the usage figures', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            used: 400,
            limit: 1000,
            remaining: 600,
            period_start: '2026-09-01T00:00:00Z',
            resets_at: '2026-10-01T00:00:00Z',
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    )

    const store = useUsageStore()
    await store.load()

    expect(store.usage?.remaining).toBe(600)
    expect(store.error).toBe('')
  })

  it('reports a failure without throwing', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))

    const store = useUsageStore()
    await store.load()

    expect(store.usage).toBeNull()
    expect(store.error).toBe('Could not load your usage.')
  })
})
