import { apiFetch } from '@/lib/api'

export interface Usage {
  used: number
  limit: number | null
  remaining: number | null
  period_start: string
  resets_at: string
}

export function getUsage(): Promise<Usage> {
  return apiFetch<Usage>('/usage')
}
