<script setup lang="ts">
import type { UIMessage } from 'ai'

import { messageText } from '../messages'
import MessageActions from './MessageActions.vue'
import MessageContent from './MessageContent.vue'

defineProps<{ messages: UIMessage[]; working: boolean }>()

const emit = defineEmits<{
  quote: [message: UIMessage]
  edit: [message: UIMessage]
  regenerate: [message: UIMessage]
}>()
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
      class="turn flex flex-col gap-1.5"
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
      <MessageActions
        :message="message"
        :role="message.role === 'user' ? 'user' : 'assistant'"
        @quote="emit('quote', message)"
        @edit="emit('edit', message)"
        @regenerate="emit('regenerate', message)"
      />
    </div>

    <div v-if="working" role="status" class="flex items-center gap-2 text-body-sm text-subtext">
      <span class="h-2 w-2 animate-pulse rounded-full bg-ink/40 motion-reduce:animate-none" />
      Assistant is working…
    </div>
  </div>
</template>

<style scoped>
/* Opacity rather than visibility: a hidden-but-focusable control keeps the row
   reachable by keyboard, and `:focus-within` reveals it once Tab lands inside.
   Never `group-*` — those variants are inert in this build. Coarse pointers
   have no hover, so the row is always visible there. */
.turn :deep(.message-actions) {
  opacity: 0;
  pointer-events: none;
}

.turn:hover :deep(.message-actions),
.turn:focus-within :deep(.message-actions) {
  opacity: 1;
  pointer-events: auto;
}

@media (pointer: coarse) {
  .turn :deep(.message-actions) {
    opacity: 1;
    pointer-events: auto;
  }
}
</style>
