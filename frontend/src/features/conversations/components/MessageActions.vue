<script setup lang="ts">
/**
 * Tertiary icon row under a Conversation Turn (DESIGN.md — Message Actions).
 * MessageList owns the turn, so it also owns the hover/focus-within reveal and
 * hides this row at rest; here the row only carries the transition, because it
 * is the element whose opacity moves. (`group-*` would be the Tailwind idiom for
 * that reveal and is inert in this build.) The row is visible by default: a
 * consumer that is not a turn gets the actions rather than an invisible row.
 *
 * Copy is handled here because it owns its transient "Copied" confirmation; the
 * other actions are the transcript's to perform, so they leave as events.
 */
import type { UIMessage } from 'ai'
import Button from 'primevue/button'
import { computed, onBeforeUnmount, ref } from 'vue'

import IconCheck from '~icons/lucide/check'
import IconCopy from '~icons/lucide/copy'
import IconPencil from '~icons/lucide/pencil'
import IconQuote from '~icons/lucide/quote'
import IconRefreshCw from '~icons/lucide/refresh-cw'

import { copyToClipboard } from '@/lib/clipboard'

import { messageText } from '../messages'

const props = defineProps<{ message: UIMessage; role: 'user' | 'assistant' }>()
const emit = defineEmits<{ quote: []; edit: []; regenerate: [] }>()

const copied = ref(false)
const copyLabel = computed(() => (copied.value ? 'Copied' : 'Copy message'))
let copyTimer: ReturnType<typeof setTimeout> | undefined

async function onCopy(): Promise<void> {
  if (!(await copyToClipboard(messageText(props.message)))) return
  copied.value = true
  clearTimeout(copyTimer)
  copyTimer = setTimeout(() => {
    copied.value = false
  }, 1500)
}

onBeforeUnmount(() => {
  clearTimeout(copyTimer)
})
</script>

<template>
  <div
    class="message-actions flex items-center gap-1 transition-opacity motion-reduce:transition-none"
  >
    <Button
      text
      rounded
      :aria-label="copyLabel"
      class="!size-8 !p-0"
      v-tooltip="{ value: copyLabel, class: 'text-body-sm' }"
      @click="onCopy"
    >
      <IconCheck v-if="copied" class="size-4 shrink-0 text-icon" stroke-width="2" />
      <IconCopy v-else class="size-4 shrink-0 text-icon" stroke-width="2" />
    </Button>

    <Button
      text
      rounded
      aria-label="Quote message"
      class="!size-8 !p-0"
      v-tooltip="{ value: 'Quote message', class: 'text-body-sm' }"
      @click="emit('quote')"
    >
      <IconQuote class="size-4 shrink-0 text-icon" stroke-width="2" />
    </Button>

    <Button
      v-if="role === 'user'"
      text
      rounded
      aria-label="Edit message"
      class="!size-8 !p-0"
      v-tooltip="{ value: 'Edit message', class: 'text-body-sm' }"
      @click="emit('edit')"
    >
      <IconPencil class="size-4 shrink-0 text-icon" stroke-width="2" />
    </Button>
    <Button
      v-else
      text
      rounded
      aria-label="Regenerate response"
      class="!size-8 !p-0"
      v-tooltip="{ value: 'Regenerate response', class: 'text-body-sm' }"
      @click="emit('regenerate')"
    >
      <IconRefreshCw class="size-4 shrink-0 text-icon" stroke-width="2" />
    </Button>

    <span class="sr-only" aria-live="polite">{{ copied ? 'Copied' : '' }}</span>
  </div>
</template>
