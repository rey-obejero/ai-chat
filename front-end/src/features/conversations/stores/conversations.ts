import { defineStore } from 'pinia'
import { ref } from 'vue'

import { createConversation, listConversations, type Conversation } from '../api'

export type { Conversation } from '../api'

export const useConversationsStore = defineStore('conversations', () => {
  const conversations = ref<Conversation[]>([])
  const loading = ref(false)
  const error = ref('')
  // A message typed before its conversation exists; consumed once the
  // conversation view mounts and can send it (ADR-0022).
  const queuedMessage = ref('')

  async function load(): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      const loaded = await listConversations()
      conversations.value = [...loaded].sort((a, b) => b.created_at.localeCompare(a.created_at))
    } catch {
      error.value = 'Could not load your conversations.'
    } finally {
      loading.value = false
    }
  }

  async function create(): Promise<Conversation> {
    const created = await createConversation()
    conversations.value = [created, ...conversations.value]
    return created
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
    load,
    create,
    queueMessage,
    takeQueuedMessage,
  }
})
