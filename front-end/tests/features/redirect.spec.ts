import { describe, expect, it } from 'vitest'

import { safeRedirect } from '@/lib/redirect'

const FALLBACK = { name: 'conversations' } as const

describe('safeRedirect', () => {
  it('passes a same-origin path through', () => {
    expect(safeRedirect('/application/conversations/abc', FALLBACK)).toBe(
      '/application/conversations/abc',
    )
  })

  // The whole point of the function: `//evil.example` is protocol-relative, so
  // the router would follow it to another host.
  it('rejects a protocol-relative value', () => {
    expect(safeRedirect('//evil.example', FALLBACK)).toBe(FALLBACK)
  })

  it('rejects an absolute URL', () => {
    expect(safeRedirect('https://evil.example', FALLBACK)).toBe(FALLBACK)
  })

  it('rejects a bare relative path', () => {
    expect(safeRedirect('conversations', FALLBACK)).toBe(FALLBACK)
  })

  it('rejects a backslash, which some parsers normalise to a slash', () => {
    expect(safeRedirect('/\\evil.example', FALLBACK)).toBe(FALLBACK)
  })

  it.each([undefined, null, 42, ['/a']])('falls back for %p', (value) => {
    expect(safeRedirect(value, FALLBACK)).toBe(FALLBACK)
  })
})
