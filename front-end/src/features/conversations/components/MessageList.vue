<script setup lang="ts">
import type { UIMessage } from 'ai'

import { messageText } from '../messages'

defineProps<{ messages: UIMessage[] }>()
</script>

<template>
  <div class="mx-auto flex w-full max-w-2xl flex-col gap-6">
    <div v-for="message in messages" :key="message.id" class="flex flex-col gap-1">
      <span class="text-caption uppercase tracking-wide text-subtext">{{ message.role }}</span>
      <p class="whitespace-pre-wrap text-body text-ink">{{ messageText(message) }}</p>
    </div>
  </div>
</template>
