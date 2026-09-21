import { defineStore } from 'pinia'
import { ref } from 'vue'

import { listConversations, type Conversation } from '../api'

export type { Conversation } from '../api'

export const useConversationsStore = defineStore('conversations', () => {
  const conversations = ref<Conversation[]>([])
  const loading = ref(false)
  const error = ref('')

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

  return {
    conversations,
    loading,
    error,
    load,
  }
})
