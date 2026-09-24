<script setup lang="ts">
import Dialog from 'primevue/dialog'
import { watch } from 'vue'

import { UsagePanel, useUsageStore } from '@/features/usage'
import ProviderSection from './ProviderSection.vue'

const visible = defineModel<boolean>({ required: true })

const usage = useUsageStore()

// Fetch fresh figures each time the modal opens.
watch(visible, (open) => {
  if (open) {
    void usage.load()
  }
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
