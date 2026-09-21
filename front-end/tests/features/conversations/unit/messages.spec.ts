import type { UIMessage } from 'ai'
import { describe, expect, it } from 'vitest'

import {
  describeError,
  lastUserText,
  messageText,
  toUIMessages,
} from '@/features/conversations/messages'
import { ApiError } from '@/lib/api'

describe('conversation message helpers', () => {
  it('joins the text parts of a message', () => {
    const message: UIMessage = {
      id: 'm1',
      role: 'assistant',
      parts: [
        { type: 'text', text: 'Hello ' },
        { type: 'text', text: 'world' },
      ],
    }

    expect(messageText(message)).toBe('Hello world')
  })

  it('returns the newest user text, ignoring earlier turns', () => {
    const messages: UIMessage[] = [
      { id: 'm1', role: 'user', parts: [{ type: 'text', text: 'first' }] },
      { id: 'm2', role: 'assistant', parts: [{ type: 'text', text: 'reply' }] },
      { id: 'm3', role: 'user', parts: [{ type: 'text', text: 'second' }] },
    ]

    expect(lastUserText(messages)).toBe('second')
  })

  it('returns empty text when there is no user message', () => {
    expect(lastUserText([])).toBe('')
  })

  it('maps persisted history into UI messages', () => {
    const history = [
      { id: 'a', role: 'user' as const, content: 'hi', created_at: '2026-01-01T00:00:00Z' },
      { id: 'b', role: 'assistant' as const, content: 'hello', created_at: '2026-01-01T00:00:01Z' },
    ]

    expect(toUIMessages(history)).toEqual([
      { id: 'a', role: 'user', parts: [{ type: 'text', text: 'hi' }] },
      { id: 'b', role: 'assistant', parts: [{ type: 'text', text: 'hello' }] },
    ])
  })
})

describe('describeError', () => {
  it('turns a known problem code into readable copy', () => {
    const error = new ApiError({
      type: 'about:blank',
      title: 'Too Many Requests',
      status: 429,
      detail: 'Rate limit exceeded.',
      code: 'RATE_LIMITED',
    })

    expect(describeError(error)).toBe(
      'Too many messages too quickly. Wait a moment, then try again.',
    )
  })

  it('falls back to the server detail for an unmapped code', () => {
    const error = new ApiError({
      type: 'about:blank',
      title: 'Conflict',
      status: 409,
      detail: 'Conversation already exists.',
      code: 'CONFLICT',
    })

    expect(describeError(error)).toBe('Conversation already exists.')
  })

  it('degrades gracefully for an unknown error', () => {
    expect(describeError(new Error('boom'))).toBe('Something went wrong. Try again.')
  })
})
