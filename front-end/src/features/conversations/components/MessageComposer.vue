<script setup lang="ts">
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'

import IconArrowUp from '~icons/lucide/arrow-up'
import IconPlus from '~icons/lucide/plus'
import IconSquare from '~icons/lucide/square'

const draft = defineModel<string>({ required: true })

defineProps<{ disabled: boolean; busy: boolean }>()
const emit = defineEmits<{ submit: []; stop: [] }>()

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    emit('submit')
  }
}
</script>

<template>
  <div
    class="mx-auto w-full max-w-2xl rounded-xl border border-line bg-paper-white p-3 transition-colors focus-within:border-ink/60"
  >
    <Textarea
      v-model="draft"
      auto-resize
      rows="1"
      placeholder="Ask a question…"
      aria-label="Message"
      class="w-full"
      @keydown="onKeydown"
    />
    <div class="mt-2 flex items-center justify-between">
      <Button text rounded aria-label="Attach a file">
        <IconPlus class="text-icon" />
      </Button>
      <Button v-if="busy" rounded severity="secondary" aria-label="Stop" @click="emit('stop')">
        <IconSquare class="text-icon" />
      </Button>
      <Button v-else rounded :disabled="disabled" aria-label="Send" @click="emit('submit')">
        <IconArrowUp />
      </Button>
    </div>
  </div>
</template>
