import { defineStore } from 'pinia'
import Session from 'supertokens-web-js/recipe/session'
import { computed, ref } from 'vue'

import { getMe, type User } from '../api'

export const useSessionStore = defineStore('session', () => {
  const user = ref<User | null>(null)
  const ready = ref(false)
  const isAuthenticated = computed(() => user.value !== null)

  async function refresh(): Promise<void> {
    try {
      if (await Session.doesSessionExist()) {
        user.value = await getMe()
      } else {
        user.value = null
      }
    } catch {
      user.value = null
    } finally {
      ready.value = true
    }
  }

  async function signOut(): Promise<void> {
    await Session.signOut()
    user.value = null
  }

  return { user, ready, isAuthenticated, refresh, signOut }
})
