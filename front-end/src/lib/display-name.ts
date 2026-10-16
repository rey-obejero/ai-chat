/**
 * The account's display name (FR-7). It is shared rather than owned by a feature
 * because `UserRead` answers with the field too: the first-run prompt, the
 * settings field and the account button all describe the same contract.
 */

/** The cap the API enforces on a display name, in characters. */
export const DISPLAY_NAME_MAX_LENGTH = 50

/**
 * The name to show for an account: what the account stores, falling back to the
 * email. Accounts are named from creation, so the fallback only covers a user
 * arriving without one rather than a state the reader should expect to see.
 */
export function displayNameOf(
  user: { display_name?: string | null; email?: string | null } | null,
): string {
  return user?.display_name?.trim() || user?.email || ''
}
