import { apiFetch } from '@/lib/api'

export interface User {
  id: string
  email: string
  created_at: string
}

export function getMe(): Promise<User> {
  return apiFetch<User>('/me')
}

export interface SocialProviders {
  providers: string[]
}

/**
 * Which social providers this deployment has credentials for.
 *
 * Read before sign-in, so the endpoint is public. It returns identifiers only,
 * never credential state.
 */
export async function listSocialProviders(): Promise<SocialProviders['providers']> {
  const response = await apiFetch<SocialProviders>('/auth/providers')
  return response.providers
}
