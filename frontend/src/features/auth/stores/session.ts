import { defineStore } from 'pinia'
import Session from 'supertokens-web-js/recipe/session'
import { computed, ref } from 'vue'

import { ApiError } from '@/lib/api'
import { getMe, updateMe, type User } from '../api'

export const useSessionStore = defineStore('session', () => {
  const user = ref<User | null>(null)
  const ready = ref(false)
  /**
   * The session check itself failed — offline or a 5xx, as opposed to the API
   * saying there is no session. `isAuthenticated` stays false either way, but
   * the guard can tell "signed out" from "could not find out" and send the user
   * to a retry screen instead of claiming they were signed out.
   */
  const unavailable = ref(false)
  const isAuthenticated = computed(() => user.value !== null)

  async function refresh(): Promise<void> {
    unavailable.value = false
    try {
      if (!(await Session.doesSessionExist())) {
        user.value = null
        return
      }
      user.value = await getMe()
    } catch (error) {
      user.value = null
      // A 401 is the API saying the session is gone; anything else (network,
      // 5xx) is the API being unreachable, which is a different answer.
      unavailable.value = !(error instanceof ApiError && error.status === 401)
    } finally {
      ready.value = true
    }
  }

  async function signOut(): Promise<void> {
    await Session.signOut()
    user.value = null
    unavailable.value = false
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
    unavailable,
    isAuthenticated,
    refresh,
    signOut,
    saveDisplayName,
    skipNamePrompt,
  }
})
