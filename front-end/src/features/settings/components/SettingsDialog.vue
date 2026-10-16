<script setup lang="ts">
import Dialog from 'primevue/dialog'
import { nextTick, watch } from 'vue'

import { UsagePanel, useUsageStore } from '@/features/usage'
import PersonalizationSection from './PersonalizationSection.vue'
import ProfileSection from './ProfileSection.vue'
import ProviderSection from './ProviderSection.vue'
import { SECTION_IDS, type SettingsSection } from '../sections'

const visible = defineModel<boolean>({ required: true })

/** The section to bring into view, when the dialog was opened for one. */
const props = defineProps<{ section?: SettingsSection | null }>()

const usage = useUsageStore()

// Fetch fresh figures each time the modal opens.
watch(visible, (open) => {
  if (open) {
    void usage.load()
  }
})

/**
 * Anchor scrolling (locked decision 8): the account menu names a section, and
 * opening the dialog puts that section in view rather than leaving the reader
 * to find it among the others.
 */
watch([visible, () => props.section], async ([open, section]) => {
  if (!open || !section) {
    return
  }
  await nextTick()
  document.getElementById(SECTION_IDS[section])?.scrollIntoView({ block: 'start' })
})
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    header="Settings"
    class="w-full max-w-lg !bg-paper-white !text-ink"
    :style="{ maxHeight: 'calc(100vh - 2rem)' }"
  >
    <div class="space-y-6">
      <section :id="SECTION_IDS.personalization" class="space-y-3">
        <h2 class="text-heading-sm font-semibold text-ink">Personalization</h2>
        <PersonalizationSection />
      </section>

      <section :id="SECTION_IDS.profile" class="space-y-3">
        <h2 class="text-heading-sm font-semibold text-ink">Profile</h2>
        <ProfileSection />
      </section>

      <section class="space-y-3">
        <h2 class="text-heading-sm font-semibold text-ink">Usage</h2>
        <UsagePanel />
      </section>

      <section class="space-y-3">
        <h2 class="text-heading-sm font-semibold text-ink">Provider</h2>
        <ProviderSection />
      </section>
    </div>
  </Dialog>
</template>
