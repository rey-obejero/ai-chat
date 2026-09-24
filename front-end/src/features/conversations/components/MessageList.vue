<script setup lang="ts">
import type { UIMessage } from 'ai'

import { messageText } from '../messages'

defineProps<{ messages: UIMessage[]; working: boolean }>()
</script>

<template>
  <div class="mx-auto flex w-full max-w-2xl flex-col gap-6">
    <div v-for="message in messages" :key="message.id" class="flex flex-col gap-1.5">
      <span class="text-caption uppercase tracking-wide text-subtext">
        {{ message.role === 'user' ? 'You' : 'Assistant' }}
      </span>
      <p class="whitespace-pre-wrap text-body leading-relaxed text-ink">
        {{ messageText(message) }}
      </p>
    </div>

    <div v-if="working" role="status" class="flex items-center gap-2 text-body-sm text-subtext">
      <span class="h-2 w-2 animate-pulse rounded-full bg-ink/40 motion-reduce:animate-none" />
      Assistant is working…
    </div>
  </div>
</template>
