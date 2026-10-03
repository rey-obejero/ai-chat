import { apiFetch } from '@/lib/api'

export interface User {
  id: string
  email: string
  created_at: string
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
