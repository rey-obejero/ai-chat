import { apiFetch } from '@/lib/api'

export interface Conversation {
  id: string
  title: string
  created_at: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
  /** The key the write that created this turn carried (ADR-0050). Null on older rows. */
  client_id?: string | null
}

export function listConversations(): Promise<Conversation[]> {
  return apiFetch<Conversation[]>('/conversations')
}

export function createConversation(): Promise<Conversation> {
  return apiFetch<Conversation>('/conversations', { method: 'POST' })
}

export function listMessages(conversationId: string): Promise<Message[]> {
  return apiFetch<Message[]>(`/conversations/${conversationId}/messages`)
}
