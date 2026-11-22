import { defineStore } from 'pinia'
import { ref } from 'vue'

import { getUsage, type Usage } from '../api'

export const useUsageStore = defineStore('usage', () => {
  const usage = ref<Usage | null>(null)
  const loading = ref(false)
  const error = ref('')

  async function load(): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      usage.value = await getUsage()
    } catch {
      error.value = 'Could not load your usage.'
    } finally {
      loading.value = false
    }
  }

  return { usage, loading, error, load }
})
