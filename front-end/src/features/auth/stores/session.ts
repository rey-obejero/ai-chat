import { defineStore } from 'pinia'
import Session from 'supertokens-web-js/recipe/session'
import { computed, ref } from 'vue'

import { getMe, updateMe, type User } from '../api'

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

  /**
   * Save the account's display name (FR-7). The write answers the first-run
   * prompt as well, so the prompt needs no second call to close; the user the
   * API returns is what every reader of the session shows next.
   */
  async function saveDisplayName(name: string): Promise<void> {
    user.value = await updateMe({ display_name: name })
  }

  /** Record that the first-run prompt was skipped, keeping the derived name. */
  async function skipNamePrompt(): Promise<void> {
    user.value = await updateMe({ name_prompt_seen: true })
  }

  return {
    user,
    ready,
    isAuthenticated,
    refresh,
    signOut,
    saveDisplayName,
    skipNamePrompt,
  }
})
