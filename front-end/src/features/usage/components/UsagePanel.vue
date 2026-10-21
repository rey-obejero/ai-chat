<script setup lang="ts">
import { computed } from 'vue'

import { useSessionStore, VerificationResend } from '@/features/auth'
import { formatTokens } from '../format'
import { useUsageStore } from '../stores/usage'

const usage = useUsageStore()
const session = useSessionStore()

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

/**
 * The reduced allowance's figures, or null when the allowance is not reduced by
 * an unverified address (FR-4, ADR-0039). The panel reports the effective limit,
 * so without this the figure below looks arbitrary for the whole period and its
 * reason only arrives when the limit is hit.
 */
const verificationGap = computed(() => {
  const value = state.value
  if (value === null || value.limit === null || value.full_limit === null) {
    return null
  }
  if (session.user?.email_verified !== false || value.limit >= value.full_limit) {
    return null
  }
  return { limit: value.limit, full: value.full_limit }
})
</script>

<template>
  <div class="space-y-3">
    <p v-if="usage.loading" class="text-body-sm text-subtext" role="status">Loading usage…</p>
    <p v-else-if="usage.error" class="text-body-sm text-subtext" role="alert">{{ usage.error }}</p>

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
        aria-label="Monthly token usage"
        :aria-valuenow="percentUsed"
        aria-valuemin="0"
        aria-valuemax="100"
      >
        <div class="h-full rounded-full bg-ink" :style="{ width: `${percentUsed}%` }" />
      </div>

      <div v-if="verificationGap" class="space-y-2 rounded-lg border border-line p-3">
        <p class="text-body-sm text-ink">
          Your email isn't verified, so your allowance is
          {{ formatTokens(verificationGap.limit) }} of {{ formatTokens(verificationGap.full) }}.
          Verify it to unlock the rest.
        </p>
        <VerificationResend />
      </div>
    </template>
  </div>
</template>
