<script setup lang="ts">
import Button from 'primevue/button'
import Menu from 'primevue/menu'
import type { MenuItem } from 'primevue/menuitem'
import Textarea from 'primevue/textarea'
import { computed, nextTick, ref, watch, type ComponentPublicInstance } from 'vue'

import IconArrowUp from '~icons/lucide/arrow-up'
import IconChevronDown from '~icons/lucide/chevron-down'
import IconPlus from '~icons/lucide/plus'
import IconSquare from '~icons/lucide/square'

import CommandPalette from './CommandPalette.vue'
import {
  applyCommand,
  commandOptionId,
  commandQuery,
  filterCommands,
  type Command,
} from '../commands'

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

/**
 * The command palette (WI-10, DESIGN.md — Command Palette). A draft that starts
 * with a slash filters the registry and the highlighted command's template
 * replaces the leading `/filter`: nothing here sends, so a lone slash cannot.
 */
const paletteOpen = ref(false)
const query = computed(() => commandQuery(draft.value))
const matches = computed(() => (query.value === null ? [] : filterCommands(query.value)))
const activeIndex = ref(0)
const activeCommand = computed(() => matches.value[activeIndex.value])
/** The filter Escape dismissed; typing a different one reopens the palette. */
const dismissedQuery = ref<string | null>(null)

watch(draft, (value) => {
  const current = commandQuery(value)

  if (current === null) {
    paletteOpen.value = false
    dismissedQuery.value = null
    return
  }

  paletteOpen.value = current !== dismissedQuery.value
})

// A new filter starts at its best match.
watch(query, () => {
  activeIndex.value = 0
})

function toggleModel(event: Event): void {
  modelMenu.value?.toggle(event)
}

function dismiss(): void {
  paletteOpen.value = false
  dismissedQuery.value = query.value
}

function select(command: Command): void {
  draft.value = applyCommand(draft.value, command)
  void focus()
}

/** True when the palette consumed the key, so it never reaches the composer. */
function paletteKeydown(event: KeyboardEvent): boolean {
  if (event.key === 'Escape') {
    event.preventDefault()
    dismiss()
    return true
  }

  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    const count = matches.value.length
    if (count > 0) {
      const step = event.key === 'ArrowDown' ? 1 : -1
      activeIndex.value = (activeIndex.value + step + count) % count
    }
    return true
  }

  // Shift+Enter is a newline and never submits, so it stays with the draft.
  if (event.key === 'Enter' && event.shiftKey) {
    return false
  }

  if (event.key === 'Enter') {
    // Enter belongs to the palette while it is open, matched or not.
    event.preventDefault()
    if (activeCommand.value) {
      select(activeCommand.value)
    }
    return true
  }

  // Tab selects only when there is a command to select.
  if (event.key === 'Tab' && activeCommand.value) {
    event.preventDefault()
    select(activeCommand.value)
    return true
  }

  return false
}

function onKeydown(event: KeyboardEvent): void {
  if (paletteOpen.value && paletteKeydown(event)) {
    return
  }

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
    if (element instanceof HTMLTextAreaElement) {
      const end = element.value.length
      element.setSelectionRange(end, end)
    }
  }
}

/** Append to the draft (Quote, FR-14) and put the caret where the text landed. */
async function insert(text: string): Promise<void> {
  draft.value = draft.value.length > 0 ? `${draft.value}\n${text}` : text
  await focus()
}

defineExpose({ focus, insert })
</script>

<template>
  <div
    class="relative rounded-xl border border-line bg-paper-white p-3 shadow-elevated motion-reduce:transition-none"
  >
    <Textarea
      ref="textarea"
      v-model="draft"
      auto-resize
      rows="2"
      placeholder="Ask anything."
      aria-label="Message"
      :aria-controls="paletteOpen ? 'command-palette' : undefined"
      :aria-activedescendant="
        paletteOpen && activeCommand ? commandOptionId(activeCommand) : undefined
      "
      class="w-full resize-none border-0 bg-transparent p-0 text-base shadow-none focus:ring-0 sm:text-sm"
      @keydown="onKeydown"
    />

    <CommandPalette
      v-if="paletteOpen"
      :commands="matches"
      :active-index="activeIndex"
      @select="select"
      @close="dismiss"
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
