<script setup lang="ts">
import Button from 'primevue/button'
import { ref } from 'vue'

import IconLoaderCircle from '~icons/lucide/loader-circle'

import { RESEND_MESSAGE, resendVerificationEmail, type ResendOutcome } from '../verification'

const sending = ref(false)
const outcome = ref<ResendOutcome | null>(null)

/**
 * Ask for another verification mail, and say what came back: a request that was
 * answered with nothing at all would leave the user guessing whether to wait.
 */
async function resend(): Promise<void> {
  outcome.value = null
  sending.value = true
  try {
    outcome.value = await resendVerificationEmail()
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="space-y-3">
    <Button
      type="button"
      severity="secondary"
      outlined
      :label="sending ? undefined : 'Resend verification email'"
      :loading="sending"
      :aria-busy="sending"
      :aria-label="sending ? 'Sending verification email' : undefined"
      class="w-full !text-sm transition-colors"
      @click="resend"
    >
      <template #loadingicon>
        <IconLoaderCircle class="animate-spin" />
      </template>
    </Button>

    <p
      v-if="outcome"
      :role="outcome === 'failed' ? 'alert' : 'status'"
      class="text-body-sm"
      :class="outcome === 'failed' ? 'text-danger' : 'text-subtext'"
    >
      {{ RESEND_MESSAGE[outcome] }}
    </p>
  </div>
</template>
