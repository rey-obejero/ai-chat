import { apiFetch } from '@/lib/api'

export interface Usage {
  used: number
  limit: number | null
  /**
   * The allowance a verified account gets. `limit` is the one actually enforced,
   * so it is lower while the address is unverified (FR-4).
   */
  full_limit: number | null
  remaining: number | null
  period_start: string
  resets_at: string
}

export function getUsage(): Promise<Usage> {
  return apiFetch<Usage>('/usage')
}
