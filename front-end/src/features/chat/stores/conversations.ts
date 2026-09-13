import { defineStore } from 'pinia'
import { ref } from 'vue'

import { apiFetch } from '@/lib/api'

export interface Conversation {
  id: string
  user_id: string
  title: string
  created_at: string
}

export const useConversationsStore = defineStore('conversations', () => {
  const conversations = ref<Conversation[]>([])
  const loading = ref(false)
  const error = ref('')

  async function load(): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      conversations.value = await apiFetch<Conversation[]>('/conversations')
    } catch {
      error.value = 'Could not load your conversations.'
    } finally {
      loading.value = false
    }
  }

  return { conversations, loading, error, load }
})
