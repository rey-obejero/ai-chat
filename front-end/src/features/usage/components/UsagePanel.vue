<script setup lang="ts">
import { computed } from 'vue'

import { formatTokens } from '../format'
import { useUsageStore } from '../stores/usage'

const usage = useUsageStore()

const state = computed(() => usage.usage)
const percentUsed = computed(() => {
  const value = state.value
  if (!value || !value.limit) {
    return 0
  }
  return Math.min(100, Math.round((value.used / value.limit) * 100))
})
const resetsAt = computed(() => {
  const value = state.value
  if (!value) {
    return ''
  }
  return new Date(value.resets_at).toLocaleDateString(undefined, {
    month: 'long',
    day: 'numeric',
  })
})
</script>

<template>
  <div class="space-y-3">
    <p v-if="usage.loading" class="text-body-sm text-subtext">Loading usage…</p>
    <p v-else-if="usage.error" class="text-body-sm text-subtext">{{ usage.error }}</p>

    <template v-else-if="state">
      <div>
        <p class="text-heading-sm font-semibold text-ink">
          <template v-if="state.remaining !== null">
            {{ formatTokens(state.remaining) }} tokens left
          </template>
          <template v-else>Unlimited tokens</template>
        </p>
        <p class="mt-1 text-body-sm text-subtext">
          <template v-if="state.limit !== null">
            {{ formatTokens(state.used) }} of {{ formatTokens(state.limit) }} used this month,
            resetting {{ resetsAt }}.
          </template>
          <template v-else>This server does not enforce a token quota.</template>
        </p>
      </div>

      <div
        v-if="state.limit !== null"
        class="h-2 w-full overflow-hidden rounded-full bg-line"
        role="progressbar"
        :aria-valuenow="percentUsed"
        aria-valuemin="0"
        aria-valuemax="100"
      >
        <div class="h-full rounded-full bg-ink" :style="{ width: `${percentUsed}%` }" />
      </div>
    </template>
  </div>
</template>
