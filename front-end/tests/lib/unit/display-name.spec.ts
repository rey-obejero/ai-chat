import { describe, expect, it } from 'vitest'

import { DISPLAY_NAME_MAX_LENGTH, displayNameOf } from '@/lib/display-name'

describe('displayNameOf', () => {
  it('returns the stored name', () => {
    expect(displayNameOf({ display_name: 'Ada Lovelace', email: 'ada@example.test' })).toBe(
      'Ada Lovelace',
    )
  })

  it('trims the stored name', () => {
    expect(displayNameOf({ display_name: '  Ada  ', email: null })).toBe('Ada')
  })

  it('falls back to the email when the name is absent or blank', () => {
    expect(displayNameOf({ display_name: null, email: 'ada@example.test' })).toBe(
      'ada@example.test',
    )
    expect(displayNameOf({ display_name: '   ', email: 'ada@example.test' })).toBe(
      'ada@example.test',
    )
  })

  it('returns an empty string for a user with neither field, and for no user', () => {
    expect(displayNameOf({ display_name: null, email: null })).toBe('')
    expect(displayNameOf(null)).toBe('')
  })
})

describe('DISPLAY_NAME_MAX_LENGTH', () => {
  it('matches the cap the API enforces', () => {
    expect(DISPLAY_NAME_MAX_LENGTH).toBe(50)
  })
})
