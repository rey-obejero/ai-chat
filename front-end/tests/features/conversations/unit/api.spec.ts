import { describe, expect, it, vi } from 'vitest'

import {
  createConversation,
  deleteConversation,
  listConversations,
  listMessages,
  updateConversation,
} from '@/features/conversations/api'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function conversationJson() {
  return {
    id: 'c1',
    title: 'First',
    created_at: '2026-01-01T00:00:00Z',
    is_pinned: false,
    is_favourite: false,
    is_archived: false,
    last_activity_at: '2026-01-01T00:00:00Z',
  }
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
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(conversationJson(), 201))
    vi.stubGlobal('fetch', fetchMock)

    const created = await createConversation()

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/v1/conversations')
    expect(init.method).toBe('POST')
    expect(created.id).toBe('c1')
  })

  it('lists a page without parameters when nothing is asked for', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ items: [], next_cursor: null }))
    vi.stubGlobal('fetch', fetchMock)

    const page = await listConversations()

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/v1/conversations')
    expect(init.method ?? 'GET').toBe('GET')
    expect(page).toEqual({ items: [], next_cursor: null })
  })

  it('passes the search term and the archived flag', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ items: [], next_cursor: null }))
    vi.stubGlobal('fetch', fetchMock)

    await listConversations({ q: 'milk & honey', includeArchived: true })

    const [url] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/v1/conversations?q=milk+%26+honey&include_archived=true')
  })

  it('passes the cursor when paging', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ items: [], next_cursor: null }))
    vi.stubGlobal('fetch', fetchMock)

    await listConversations({ cursor: 'cursor-1' })

    const [url] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/v1/conversations?cursor=cursor-1')
  })

  it('renames with PATCH and the changed field alone', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(conversationJson()))
    vi.stubGlobal('fetch', fetchMock)

    const updated = await updateConversation('abc', { title: 'Renamed' })

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/v1/conversations/abc')
    expect(init.method).toBe('PATCH')
    expect(init.body).toBe(JSON.stringify({ title: 'Renamed' }))
    expect(updated.id).toBe('c1')
  })

  it('pins with PATCH and the flag alone', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(conversationJson()))
    vi.stubGlobal('fetch', fetchMock)

    await updateConversation('abc', { is_pinned: true })

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(init.body).toBe(JSON.stringify({ is_pinned: true }))
  })

  it('deletes with DELETE and settles on the empty 204', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(deleteConversation('abc')).resolves.toBeUndefined()

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/v1/conversations/abc')
    expect(init.method).toBe('DELETE')
  })
})
