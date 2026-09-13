import { apiFetch } from '@/lib/api'

export interface User {
  id: string
  email: string
  created_at: string
}

export function getMe(): Promise<User> {
  return apiFetch<User>('/me')
}
