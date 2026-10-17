import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  createConversation,
  deleteConversation,
  listConversations,
  updateConversation,
  type Conversation,
  type ConversationPage,
} from '@/features/conversations/api'
import { useConversationsStore } from '@/features/conversations/stores/conversations'

vi.mock('@/features/conversations/api', () => ({
  createConversation: vi.fn(),
  deleteConversation: vi.fn(),
  listConversations: vi.fn(),
  updateConversation: vi.fn(),
}))

const listMock = vi.mocked(listConversations)
const updateMock = vi.mocked(updateConversation)
const deleteMock = vi.mocked(deleteConversation)
const createMock = vi.mocked(createConversation)

function conversation(overrides: Partial<Conversation> & { id: string }): Conversation {
  return {
    title: `Conversation ${overrides.id}`,
    created_at: '2026-01-01T00:00:00Z',
    is_pinned: false,
    is_favourite: false,
    is_archived: false,
    model: null,
    last_activity_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

function page(items: Conversation[], nextCursor: string | null = null): ConversationPage {
  return { items, next_cursor: nextCursor }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.resetAllMocks()
})

describe('conversations store memory', () => {
  it('remembers a row a later search drops from the list', async () => {
    listMock.mockResolvedValue(page([conversation({ id: 'alpha', title: 'alpha note' })]))
    const store = useConversationsStore()
    await store.load()

    // A search the open conversation does not match: the list stops holding it,
    // while the header title and the model guard still need that row (FR-11, FR-23).
    listMock.mockResolvedValue(page([conversation({ id: 'beta', title: 'beta note' })]))
    await store.search('beta')

    expect(store.conversations.map((row) => row.id)).toEqual(['beta'])
    expect(store.known['alpha']?.title).toBe('alpha note')
  })

  it('forgets a row it deleted', async () => {
    listMock.mockResolvedValue(page([conversation({ id: 'alpha' })]))
    deleteMock.mockResolvedValue(undefined)
    const store = useConversationsStore()
    await store.load()

    await store.remove('alpha')

    expect(store.known['alpha']).toBeUndefined()
  })
})

describe('conversations store loading', () => {
  it('loads the first page pinned-first, then by most recent activity', async () => {
    listMock.mockResolvedValue(
      page([
        conversation({ id: 'older', last_activity_at: '2026-01-01T00:00:00Z' }),
        conversation({ id: 'pinned', last_activity_at: '2025-12-01T00:00:00Z', is_pinned: true }),
        conversation({ id: 'recent', last_activity_at: '2026-02-01T00:00:00Z' }),
      ]),
    )
    const store = useConversationsStore()

    await store.load()

    expect(listMock).toHaveBeenCalledWith({ q: '', includeArchived: true })
    expect(store.conversations.map((item) => item.id)).toEqual(['pinned', 'recent', 'older'])
  })

  it('splits the rows into pinned, recents and archived', async () => {
    listMock.mockResolvedValue(
      page([
        conversation({ id: 'a' }),
        conversation({ id: 'b', is_pinned: true }),
        conversation({ id: 'c', is_archived: true }),
      ]),
    )
    const store = useConversationsStore()

    await store.load()

    expect(store.pinned.map((item) => item.id)).toEqual(['b'])
    expect(store.recents.map((item) => item.id)).toEqual(['a'])
    expect(store.archived.map((item) => item.id)).toEqual(['c'])
  })

  it('is pending only while the list has nothing to show', async () => {
    listMock.mockResolvedValue(page([conversation({ id: 'a' })]))
    const store = useConversationsStore()

    const loading = store.load()
    // `load` sets the flag before its first await, so this synchronous read is
    // the state the sidebar renders in.
    expect(store.pending).toBe(true)

    await loading

    expect(store.pending).toBe(false)
  })

  it('reports a failed load', async () => {
    listMock.mockRejectedValue(new Error('offline'))
    const store = useConversationsStore()

    await store.load()

    expect(store.error).toBe('Could not load your conversations.')
    expect(store.conversations).toEqual([])
  })
})

describe('conversations store search', () => {
  it('sends the trimmed term and asks for archived rows', async () => {
    listMock.mockResolvedValue(page([conversation({ id: 'a' })]))
    const store = useConversationsStore()

    await store.search('  milk  ')

    expect(listMock).toHaveBeenCalledWith({ q: 'milk', includeArchived: true })
    expect(store.query).toBe('milk')
  })

  it('states No matches only once a term has come back empty', async () => {
    listMock.mockResolvedValue(page([]))
    const store = useConversationsStore()

    await store.load()
    expect(store.noMatches).toBe(false)

    await store.search('milk')
    expect(store.noMatches).toBe(true)
  })

  it('clears the term back to the unfiltered list', async () => {
    listMock.mockResolvedValue(page([conversation({ id: 'a' })]))
    const store = useConversationsStore()

    await store.search('milk')
    await store.search('')

    expect(listMock).toHaveBeenLastCalledWith({ q: '', includeArchived: true })
    expect(store.query).toBe('')
  })
})

describe('conversations store pagination', () => {
  it('appends the next page and keeps the pinned-first order', async () => {
    listMock.mockResolvedValueOnce(
      page([conversation({ id: 'a', last_activity_at: '2026-02-01T00:00:00Z' })], 'cursor-1'),
    )
    const store = useConversationsStore()
    await store.load()
    expect(store.hasMore).toBe(true)

    listMock.mockResolvedValueOnce(
      page([
        conversation({ id: 'b', last_activity_at: '2026-03-01T00:00:00Z' }),
        conversation({ id: 'c', is_pinned: true }),
      ]),
    )
    await store.loadMore()

    expect(listMock).toHaveBeenLastCalledWith({
      q: '',
      includeArchived: true,
      cursor: 'cursor-1',
    })
    expect(store.conversations.map((item) => item.id)).toEqual(['c', 'b', 'a'])
    expect(store.hasMore).toBe(false)
  })

  it('does nothing without a cursor', async () => {
    listMock.mockResolvedValue(page([conversation({ id: 'a' })]))
    const store = useConversationsStore()
    await store.load()

    await store.loadMore()

    expect(listMock).toHaveBeenCalledTimes(1)
  })
})

describe('conversations store mutations', () => {
  beforeEach(() => {
    listMock.mockResolvedValue(
      page([
        conversation({ id: 'a' }),
        conversation({ id: 'b', last_activity_at: '2026-01-02T00:00:00Z' }),
      ]),
    )
  })

  it('renames the row in place from the write response', async () => {
    updateMock.mockResolvedValue(conversation({ id: 'a', title: 'Renamed' }))
    const store = useConversationsStore()
    await store.load()

    const renamed = await store.rename('a', '  Renamed  ')

    expect(updateMock).toHaveBeenCalledWith('a', { title: 'Renamed' })
    expect(renamed).toBe(true)
    expect(store.conversations.find((item) => item.id === 'a')?.title).toBe('Renamed')
  })

  it('pins a row and re-sorts it to the front', async () => {
    updateMock.mockResolvedValue(conversation({ id: 'a', is_pinned: true }))
    const store = useConversationsStore()
    await store.load()
    // b is the more recent of the two, so it leads before the pin.
    expect(store.conversations.map((item) => item.id)).toEqual(['b', 'a'])

    await store.togglePin('a')

    expect(updateMock).toHaveBeenCalledWith('a', { is_pinned: true })
    expect(store.conversations.map((item) => item.id)).toEqual(['a', 'b'])
    expect(store.pinned.map((item) => item.id)).toEqual(['a'])
    expect(store.recents.map((item) => item.id)).toEqual(['b'])
  })

  it('unpins a pinned row and drops it back into the activity order', async () => {
    listMock.mockResolvedValue(
      page([
        conversation({ id: 'pinned', is_pinned: true, last_activity_at: '2025-01-01T00:00:00Z' }),
        conversation({ id: 'recent', last_activity_at: '2026-02-01T00:00:00Z' }),
      ]),
    )
    updateMock.mockResolvedValue(
      conversation({ id: 'pinned', last_activity_at: '2025-01-01T00:00:00Z' }),
    )
    const store = useConversationsStore()
    await store.load()

    await store.togglePin('pinned')

    expect(updateMock).toHaveBeenCalledWith('pinned', { is_pinned: false })
    expect(store.conversations.map((item) => item.id)).toEqual(['recent', 'pinned'])
  })

  it('favourites a row without moving it', async () => {
    updateMock.mockResolvedValue(conversation({ id: 'b', is_favourite: true }))
    const store = useConversationsStore()
    await store.load()

    await store.toggleFavourite('b')

    expect(updateMock).toHaveBeenCalledWith('b', { is_favourite: true })
    expect(store.conversations.find((item) => item.id === 'b')?.is_favourite).toBe(true)
    expect(store.recents.map((item) => item.id)).toEqual(['b', 'a'])
  })

  it('archives a row out of the recents list and back', async () => {
    updateMock.mockResolvedValue(conversation({ id: 'a', is_archived: true }))
    const store = useConversationsStore()
    await store.load()

    await store.toggleArchive('a')

    expect(updateMock).toHaveBeenCalledWith('a', { is_archived: true })
    expect(store.recents.map((item) => item.id)).toEqual(['b'])
    expect(store.archived.map((item) => item.id)).toEqual(['a'])
  })

  it('drops a row once the delete succeeds', async () => {
    deleteMock.mockResolvedValue(undefined)
    const store = useConversationsStore()
    await store.load()

    const removed = await store.remove('a')

    expect(deleteMock).toHaveBeenCalledWith('a')
    expect(removed).toBe(true)
    expect(store.conversations.map((item) => item.id)).toEqual(['b'])
  })

  it('keeps the row and reports a failed write', async () => {
    updateMock.mockRejectedValue(new Error('nope'))
    deleteMock.mockRejectedValue(new Error('nope'))
    const store = useConversationsStore()
    await store.load()

    expect(await store.rename('a', 'Renamed')).toBe(false)
    expect(store.error).toBe('Could not update the conversation.')
    expect(store.conversations.find((item) => item.id === 'a')?.title).toBe('Conversation a')

    expect(await store.remove('a')).toBe(false)
    expect(store.error).toBe('Could not delete the conversation.')
    expect(store.conversations.map((item) => item.id)).toEqual(['b', 'a'])
  })

  it('ignores a toggle for a row it does not have', async () => {
    const store = useConversationsStore()
    await store.load()

    expect(await store.togglePin('missing')).toBe(false)
    expect(updateMock).not.toHaveBeenCalled()
  })
})

describe('conversations store create', () => {
  it('keeps a new conversation below the pinned ones', async () => {
    listMock.mockResolvedValue(page([conversation({ id: 'pinned', is_pinned: true })]))
    createMock.mockResolvedValue(
      conversation({ id: 'new', last_activity_at: '2026-06-01T00:00:00Z' }),
    )
    const store = useConversationsStore()
    await store.load()

    const created = await store.create()

    expect(created.id).toBe('new')
    expect(store.conversations.map((item) => item.id)).toEqual(['pinned', 'new'])
  })
})
