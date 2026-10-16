/**
 * The account's personalisation vocabulary (FR-24, FR-25). It is shared rather
 * than owned by the settings feature because `UserRead` answers with both fields
 * too: the settings form and the session's user describe the same contract.
 */

/** The styles `PUT /preferences` accepts, in the order the form offers them. */
export const RESPONSE_STYLES = ['default', 'concise', 'detailed', 'formal', 'casual'] as const

export type ResponseStyle = (typeof RESPONSE_STYLES)[number]

/** The styles as a select offers them: the stored value and its label. */
export const RESPONSE_STYLE_OPTIONS = RESPONSE_STYLES.map((value) => ({
  value,
  label: value.charAt(0).toUpperCase() + value.slice(1),
}))

/** The cap on the instructions the API accepts, in characters. */
export const INSTRUCTIONS_MAX_LENGTH = 2000
