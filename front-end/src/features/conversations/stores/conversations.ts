import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import {
  createConversation,
  deleteConversation,
  listConversations,
  updateConversation,
  type Conversation,
  type ConversationUpdate,
  type ListConversationsParams,
} from '../api'

export type { Conversation } from '../api'

/**
 * Pinned first, then most recent activity (locked decision 1). The API answers
 * in the same order, but a PATCH returns the one row it changed and a pin is
 * what decides that row's place, so every mutation re-sorts here.
 */
function byPinnedThenActivity(a: Conversation, b: Conversation): number {
  if (a.is_pinned !== b.is_pinned) {
    return a.is_pinned ? -1 : 1
  }
  return b.last_activity_at.localeCompare(a.last_activity_at)
}

export const useConversationsStore = defineStore('conversations', () => {
  const conversations = ref<Conversation[]>([])
  const loading = ref(false)
  const error = ref('')
  /** The term the current list is the answer to; empty is the unfiltered list. */
  const query = ref('')
  const nextCursor = ref<string | null>(null)
  // A message typed before its conversation exists; consumed once the
  // conversation view mounts and can send it (ADR-0022).
  const queuedMessage = ref('')

  // The sidebar's three sections. Archived rows are fetched (`include_archived`)
  // and split out here rather than in a second request; a pinned row that is
  // also archived belongs to Archived, so unarchiving it returns it to Pinned.
  const pinned = computed(() =>
    conversations.value.filter(
      (conversation) => conversation.is_pinned && !conversation.is_archived,
    ),
  )
  const recents = computed(() =>
    conversations.value.filter(
      (conversation) => !conversation.is_pinned && !conversation.is_archived,
    ),
  )
  const archived = computed(() =>
    conversations.value.filter((conversation) => conversation.is_archived),
  )
  const hasMore = computed(() => nextCursor.value !== null)
  /** The first page is on its way and there is nothing to show yet. */
  const pending = computed(() => loading.value && conversations.value.length === 0)
  const noMatches = computed(
    () =>
      query.value.length > 0 &&
      !loading.value &&
      error.value === '' &&
      conversations.value.length === 0,
  )

  function apply(items: Conversation[]): void {
    conversations.value = [...items].sort(byPinnedThenActivity)
  }

  async function fetchPage(cursor?: string): Promise<void> {
    const params: ListConversationsParams = { q: query.value, includeArchived: true }
    if (cursor) {
      params.cursor = cursor
    }
    const page = await listConversations(params)
    nextCursor.value = page.next_cursor
    apply(cursor ? [...conversations.value, ...page.items] : page.items)
  }

  async function load(): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      await fetchPage()
    } catch {
      error.value = 'Could not load your conversations.'
    } finally {
      loading.value = false
    }
  }

  async function loadMore(): Promise<void> {
    const cursor = nextCursor.value
    if (!cursor) {
      return
    }
    loading.value = true
    error.value = ''
    try {
      await fetchPage(cursor)
    } catch {
      error.value = 'Could not load your conversations.'
    } finally {
      loading.value = false
    }
  }

  /** Filters the server-side list; `load()` is what replaces the rows. */
  async function search(term: string): Promise<void> {
    query.value = term.trim()
    await load()
  }

  async function create(model?: string): Promise<Conversation> {
    const created = await createConversation(model)
    apply([created, ...conversations.value])
    return created
  }

  /**
   * One row's partial update, re-sorted into place. Returns whether the write
   * landed, so the caller can keep an inline editor open when it did not.
   */
  async function update(id: string, patch: ConversationUpdate): Promise<boolean> {
    error.value = ''
    try {
      const updated = await updateConversation(id, patch)
      apply(
        conversations.value.map((conversation) =>
          conversation.id === id ? updated : conversation,
        ),
      )
      return true
    } catch {
      error.value = 'Could not update the conversation.'
      return false
    }
  }

  function rename(id: string, title: string): Promise<boolean> {
    return update(id, { title: title.trim() })
  }

  /**
   * Point a conversation at another model (FR-23). The server persists the
   * switch as a system message; the view shows the matching caption.
   */
  function setModel(id: string, model: string): Promise<boolean> {
    return update(id, { model })
  }

  function togglePin(id: string): Promise<boolean> {
    const conversation = conversations.value.find((item) => item.id === id)
    return conversation
      ? update(id, { is_pinned: !conversation.is_pinned })
      : Promise.resolve(false)
  }

  function toggleFavourite(id: string): Promise<boolean> {
    const conversation = conversations.value.find((item) => item.id === id)
    return conversation
      ? update(id, { is_favourite: !conversation.is_favourite })
      : Promise.resolve(false)
  }

  function toggleArchive(id: string): Promise<boolean> {
    const conversation = conversations.value.find((item) => item.id === id)
    return conversation
      ? update(id, { is_archived: !conversation.is_archived })
      : Promise.resolve(false)
  }

  async function remove(id: string): Promise<boolean> {
    error.value = ''
    try {
      await deleteConversation(id)
    } catch {
      error.value = 'Could not delete the conversation.'
      return false
    }
    conversations.value = conversations.value.filter((conversation) => conversation.id !== id)
    return true
  }

  function queueMessage(text: string): void {
    queuedMessage.value = text
  }

  function takeQueuedMessage(): string {
    const text = queuedMessage.value
    queuedMessage.value = ''
    return text
  }

  return {
    conversations,
    loading,
    error,
    query,
    nextCursor,
    pinned,
    recents,
    archived,
    hasMore,
    pending,
    noMatches,
    load,
    loadMore,
    search,
    create,
    rename,
    setModel,
    togglePin,
    toggleFavourite,
    toggleArchive,
    remove,
    queueMessage,
    takeQueuedMessage,
  }
})
