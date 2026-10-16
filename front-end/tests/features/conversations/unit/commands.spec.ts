import { describe, expect, it } from 'vitest'

import {
  applyCommand,
  COMMANDS,
  commandQuery,
  filterCommands,
  type Command,
} from '@/features/conversations/commands'

/** The registry is fixed, so a missing id is a broken test rather than a case. */
function command(id: string): Command {
  const found = COMMANDS.find((item) => item.id === id)
  if (!found) {
    throw new Error(`unknown command: ${id}`)
  }
  return found
}

describe('the command registry', () => {
  it('ships the four built-ins, all prompts', () => {
    expect(COMMANDS.map((item) => item.id)).toEqual([
      'explain',
      'summarize',
      'rewrite',
      'translate',
    ])
    expect(COMMANDS.every((item) => item.kind === 'prompt')).toBe(true)
  })

  it('gives every command a leading-slash label, a description and a template', () => {
    for (const item of COMMANDS) {
      expect(item.label).toBe(`/${item.id}`)
      expect(item.description.length).toBeGreaterThan(0)
      expect(item.template.length).toBeGreaterThan(0)
    }
  })

  it('carries the promised templates', () => {
    expect(command('explain').template).toBe('Explain the following in simple terms:\n\n')
    expect(command('summarize').template).toBe(
      'Summarize the following, keeping the key points:\n\n',
    )
    expect(command('rewrite').template).toBe('Rewrite the following more clearly:\n\n')
    expect(command('translate').template).toBe('Translate the following into English:\n\n')
  })
})

describe('commandQuery', () => {
  it('reads the filter between the leading slash and the first space', () => {
    expect(commandQuery('/')).toBe('')
    expect(commandQuery('/trans')).toBe('trans')
    expect(commandQuery('/trans hello')).toBe('trans')
    expect(commandQuery('/trans\nhello')).toBe('trans')
  })

  it('is not an invocation when the slash is not leading', () => {
    expect(commandQuery('')).toBeNull()
    expect(commandQuery('hello')).toBeNull()
    expect(commandQuery('see /api/v1')).toBeNull()
  })
})

describe('filterCommands', () => {
  it('lists every command for an empty filter', () => {
    expect(filterCommands('')).toHaveLength(COMMANDS.length)
  })

  it('filters case-insensitively, ignoring the surrounding space', () => {
    expect(filterCommands('TRANS').map((item) => item.id)).toEqual(['translate'])
    expect(filterCommands('Summ').map((item) => item.id)).toEqual(['summarize'])
    expect(filterCommands(' summ ').map((item) => item.id)).toEqual(['summarize'])
  })

  it('matches the label as well as the id', () => {
    // 'xpl' is in the label only: the id is 'explain'.
    expect(filterCommands('xpl').map((item) => item.label)).toEqual(['/explain'])
  })

  it('returns nothing when no command matches', () => {
    expect(filterCommands('zzz')).toEqual([])
  })
})

describe('applyCommand', () => {
  it('replaces the leading filter with the template', () => {
    expect(applyCommand('/trans', command('translate'))).toBe(command('translate').template)
    expect(applyCommand('/', command('explain'))).toBe(command('explain').template)
  })

  it('keeps the text that followed the filter', () => {
    // Locked: the remainder loses only the space that separated it from the
    // filter, so `/trans hello` keeps `hello` and drops the stray space.
    expect(applyCommand('/trans hello', command('translate'))).toBe(
      'Translate the following into English:\n\nhello',
    )
  })

  it('keeps multi-line text that followed the filter', () => {
    expect(applyCommand('/sum\nhello', command('summarize'))).toBe(
      `${command('summarize').template}hello`,
    )
  })

  it('falls back to the template when the draft is not an invocation', () => {
    expect(applyCommand('hello', command('explain'))).toBe(command('explain').template)
  })
})
