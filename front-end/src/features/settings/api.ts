import { apiFetch } from '@/lib/api'
import type { ResponseStyle } from '@/lib/preferences'

/** The fields a preference write may change; everything else is left as it is. */
export interface PreferencesUpdate {
  instructions?: string
  response_style?: ResponseStyle
}

/**
 * Save the account's standing instructions and response style (FR-24, FR-25).
 * Both shape future replies only — nothing already said is rewritten. The
 * session's user is refetched by the caller, so the form reads the stored value
 * back rather than trusting what it sent.
 */
export function updatePreferences(preferences: PreferencesUpdate): Promise<void> {
  return apiFetch<void>('/preferences', {
    method: 'PUT',
    body: JSON.stringify(preferences),
  })
}
