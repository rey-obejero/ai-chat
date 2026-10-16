import { apiFetch } from '@/lib/api'
import type { ResponseStyle } from '@/lib/preferences'

export interface User {
  id: string
  email: string
  created_at: string
  /**
   * The name shown for the account (FR-7). It is derived from the email when the
   * account is created, so it is never blank; the first-run prompt and the
   * settings Profile field are the two ways to change it.
   */
  display_name: string
  /** Whether the first-run name prompt has been answered (FR-7). */
  name_prompt_seen: boolean
  /** The account's standing instructions, or null when there are none (FR-24). */
  instructions: string | null
  /** The style replies are written in (FR-25); `default` adds no prompt text. */
  response_style: ResponseStyle
}

export function getMe(): Promise<User> {
  return apiFetch<User>('/me')
}

/** The identity fields a profile write may change; everything else is left as it is. */
export interface ProfileUpdate {
  display_name?: string
  name_prompt_seen?: boolean
}

/**
 * Save the account's display name and/or record that the first-run prompt was
 * answered (FR-7). Saving a name answers the prompt too, so a write that sends
 * only the name still closes it; the users these fields name come back rather
 * than being guessed at.
 */
export function updateMe(update: ProfileUpdate): Promise<User> {
  return apiFetch<User>('/me', {
    method: 'PATCH',
    body: JSON.stringify(update),
  })
}

export interface SocialProvider {
  id: string
  name: string
}

interface SocialProviders {
  providers: SocialProvider[]
}

/**
 * Which social providers this deployment has credentials for.
 *
 * Read before sign-in, so the endpoint is public. It returns identifiers and
 * display names only, never credential state. The name comes from the backend
 * so a label is not defined in two places.
 */
export async function listSocialProviders(): Promise<SocialProvider[]> {
  const response = await apiFetch<SocialProviders>('/auth/providers')
  return response.providers
}
