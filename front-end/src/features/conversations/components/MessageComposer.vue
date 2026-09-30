<script setup lang="ts">
import Button from 'primevue/button'
import Menu from 'primevue/menu'
import type { MenuItem } from 'primevue/menuitem'
import Textarea from 'primevue/textarea'
import { nextTick, ref, type ComponentPublicInstance } from 'vue'

import IconArrowUp from '~icons/lucide/arrow-up'
import IconChevronDown from '~icons/lucide/chevron-down'
import IconPlus from '~icons/lucide/plus'
import IconSquare from '~icons/lucide/square'

const draft = defineModel<string>({ required: true })

defineProps<{ disabled: boolean; busy: boolean }>()
const emit = defineEmits<{ submit: []; stop: [] }>()

const textarea = ref<ComponentPublicInstance | null>(null)
const modelMenu = ref()

// One model is served (llm_model is a single server setting), so Auto is the
// only entry. The dropdown is the affordance; switching needs the API to accept
// a model first. See DESIGN.md — Model Selector.
const model = ref('Auto')

const modelItems: MenuItem[] = [{ label: 'Auto' }]

function toggleModel(event: Event): void {
  modelMenu.value?.toggle(event)
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    emit('submit')
  }
}

async function focus(): Promise<void> {
  await nextTick()
  const element = textarea.value?.$el
  if (element instanceof HTMLElement) {
    element.focus()
  }
}

defineExpose({ focus })
</script>

<template>
  <div
    class="rounded-xl border border-line bg-paper-white p-3 shadow-elevated motion-reduce:transition-none"
  >
    <Textarea
      ref="textarea"
      v-model="draft"
      auto-resize
      rows="2"
      placeholder="Ask anything."
      aria-label="Message"
      class="w-full resize-none border-0 bg-transparent p-0 text-base shadow-none focus:ring-0 sm:text-sm"
      @keydown="onKeydown"
    />

    <div class="mt-3 flex items-center justify-between gap-3">
      <Button
        text
        rounded
        aria-label="Attach a file"
        class="!size-8 !p-0"
        v-tooltip="{ value: 'Attach a file', class: 'text-body-sm' }"
      >
        <IconPlus class="size-4 shrink-0 text-icon" stroke-width="2" />
      </Button>

      <div class="flex items-center gap-2">
        <!-- Tertiary: no fill at rest, Line at 40% on hover, no border. -->
        <Button
          text
          aria-haspopup="true"
          aria-controls="model_menu"
          class="rounded-lg !px-2 !py-1.5 !text-body-sm"
          @click="toggleModel"
        >
          <span>{{ model }}</span>
          <IconChevronDown class="ml-1.5 size-4 shrink-0 text-icon" stroke-width="2" />
        </Button>

        <Button
          v-if="busy"
          rounded
          severity="secondary"
          aria-label="Stop"
          class="!size-8 !p-0"
          v-tooltip="{ value: 'Stop generating', class: 'text-body-sm' }"
          @click="emit('stop')"
        >
          <IconSquare class="size-4 shrink-0" stroke-width="2" />
        </Button>
        <Button
          v-else
          rounded
          :disabled="disabled"
          aria-label="Send"
          class="!size-8 !p-0"
          v-tooltip="{ value: 'Send message', class: 'text-body-sm' }"
          @click="emit('submit')"
        >
          <IconArrowUp class="size-4 shrink-0" stroke-width="2" />
        </Button>
      </div>
      <Menu id="model_menu" ref="modelMenu" :model="modelItems" :popup="true" />
    </div>
  </div>
</template>
