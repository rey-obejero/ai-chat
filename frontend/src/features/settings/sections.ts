/**
 * The settings dialog's sections, named so a caller can ask for one to be
 * brought into view — the account menu's Personalization and Profile items do
 * (locked decision 8).
 */
export type SettingsSection = 'personalization' | 'profile'

/** The element id each section carries, which is how the dialog finds it. */
export const SECTION_IDS: Record<SettingsSection, string> = {
  personalization: 'settings-personalization',
  profile: 'settings-profile',
}
