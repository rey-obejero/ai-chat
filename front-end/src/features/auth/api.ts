import { apiFetch } from '@/lib/api'
import type { ResponseStyle } from '@/lib/preferences'

export interface User {
  id: string
  email: string
  created_at: string
  /** The account's standing instructions, or null when there are none (FR-24). */
  instructions: string | null
  /** The style replies are written in (FR-25); `default` adds no prompt text. */
  response_style: ResponseStyle
}

export function getMe(): Promise<User> {
  return apiFetch<User>('/me')
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
