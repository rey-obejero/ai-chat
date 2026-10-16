/**
 * The settings dialog's sections, named so a caller can ask for one to be
 * brought into view — the account menu's Personalization item does (locked
 * decision 8). Profile's name section arrives with WI-4, so it is not a target
 * yet.
 */
export type SettingsSection = 'personalization'

/** The element id each section carries, which is how the dialog finds it. */
export const SECTION_IDS: Record<SettingsSection, string> = {
  personalization: 'settings-personalization',
}
