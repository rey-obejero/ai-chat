<script setup lang="ts">
import type { UIMessage } from 'ai'

import { messageText } from '../messages'
import MessageContent from './MessageContent.vue'

defineProps<{ messages: UIMessage[]; working: boolean }>()
</script>

<template>
  <div
    role="log"
    aria-label="Conversation"
    aria-live="polite"
    class="mx-auto flex min-h-full w-full max-w-3xl flex-col justify-end gap-6"
  >
    <div
      v-for="message in messages"
      :key="message.id"
      class="flex flex-col gap-1.5"
      :class="message.role === 'user' ? 'items-end' : 'items-start'"
    >
      <span
        class="text-caption uppercase tracking-wide text-subtext"
        :class="message.role === 'user' ? 'text-right' : ''"
      >
        {{ message.role === 'user' ? 'You' : 'Assistant' }}
      </span>
      <MessageContent
        :role="message.role === 'user' ? 'user' : 'assistant'"
        :text="messageText(message)"
      />
    </div>

    <div v-if="working" role="status" class="flex items-center gap-2 text-body-sm text-subtext">
      <span class="h-2 w-2 animate-pulse rounded-full bg-ink/40 motion-reduce:animate-none" />
      Assistant is working…
    </div>
  </div>
</template>
