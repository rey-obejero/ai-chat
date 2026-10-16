<script setup lang="ts">
import { VERIFICATION_NUDGE_COPY } from '../verification'
import VerificationResend from './VerificationResend.vue'
</script>

<template>
  <!-- The allowance block's answer, in place of the plain quota copy. Announced
       when it appears, because it is the reason the request was refused. -->
  <div
    class="mx-auto mt-4 flex max-w-3xl flex-col gap-3 rounded-xl border border-line bg-paper-white p-4"
  >
    <p role="alert" class="text-body-sm text-ink">{{ VERIFICATION_NUDGE_COPY }}</p>
    <VerificationResend />
  </div>
</template>
