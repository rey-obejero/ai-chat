import { apiFetch } from '@/lib/api'

export interface Conversation {
  id: string
  title: string
  created_at: string
  is_pinned: boolean
  is_favourite: boolean
  is_archived: boolean
  /** `max(messages.created_at)`, the list's ordering key (locked decision 1). */
  last_activity_at: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
  /** The key the write that created this turn carried (ADR-0050). Null on older rows. */
  client_id?: string | null
}

/** One cursor page: `next_cursor` is null once the last page has been returned. */
export interface ConversationPage {
  items: Conversation[]
  next_cursor: string | null
}

export interface ListConversationsParams {
  /** The search term, matched against message content and the title. Not stored. */
  q?: string
  /** Archived conversations are left out unless this is set. */
  includeArchived?: boolean
  cursor?: string
}

export function listConversations(params: ListConversationsParams = {}): Promise<ConversationPage> {
  const query = new URLSearchParams()
  if (params.q) {
    query.set('q', params.q)
  }
  if (params.includeArchived) {
    query.set('include_archived', 'true')
  }
  if (params.cursor) {
    query.set('cursor', params.cursor)
  }
  const search = query.toString()
  return apiFetch<ConversationPage>(`/conversations${search ? `?${search}` : ''}`)
}

/** The fields a PATCH may change; everything else is left as it is. */
export interface ConversationUpdate {
  title?: string
  is_pinned?: boolean
  is_favourite?: boolean
  is_archived?: boolean
}

export function updateConversation(id: string, update: ConversationUpdate): Promise<Conversation> {
  return apiFetch<Conversation>(`/conversations/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(update),
  })
}

export function deleteConversation(id: string): Promise<void> {
  return apiFetch<void>(`/conversations/${id}`, { method: 'DELETE' })
}

export function createConversation(): Promise<Conversation> {
  return apiFetch<Conversation>('/conversations', { method: 'POST' })
}

export function listMessages(conversationId: string): Promise<Message[]> {
  return apiFetch<Message[]>(`/conversations/${conversationId}/messages`)
}
