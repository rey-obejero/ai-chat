import { describe, expect, it, vi } from 'vitest'

import { ApiError, apiFetch } from '@/lib/api'

function jsonResponse(body: unknown, status = 200, contentType = 'application/json'): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': contentType },
  })
}

describe('apiFetch', () => {
  it('prefixes /api/v1 and sends same-origin credentials', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ id: 'u1', email: 'a@b.c' }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await apiFetch<{ id: string; email: string }>('/me')

    expect(result).toEqual({ id: 'u1', email: 'a@b.c' })
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/v1/me')
    expect(init.credentials).toBe('same-origin')
  })

  it('throws ApiError built from an RFC 9457 problem body', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(
        {
          type: 'about:blank',
          title: 'Not authenticated',
          status: 401,
          detail: 'No active session.',
          code: 'NOT_AUTHENTICATED',
        },
        401,
        'application/problem+json',
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    const failure = apiFetch('/me')
    await expect(failure).rejects.toBeInstanceOf(ApiError)
    await expect(failure).rejects.toMatchObject({
      status: 401,
      code: 'NOT_AUTHENTICATED',
      message: 'No active session.',
    })
  })
})
