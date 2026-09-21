import { describe, expect, it, vi } from 'vitest'

import { createConversation, listMessages } from '@/features/conversations/api'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('conversations api', () => {
  it('lists the messages of one conversation', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse([]))
    vi.stubGlobal('fetch', fetchMock)

    await listMessages('abc')

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/v1/conversations/abc/messages')
    expect(init.method ?? 'GET').toBe('GET')
  })

  it('creates a conversation with POST', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        jsonResponse(
          { id: 'c1', title: 'New conversation', created_at: '2026-01-01T00:00:00Z' },
          201,
        ),
      )
    vi.stubGlobal('fetch', fetchMock)

    const created = await createConversation()

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/v1/conversations')
    expect(init.method).toBe('POST')
    expect(created.id).toBe('c1')
  })
})
