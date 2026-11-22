<script setup lang="ts">
import { commandOptionId, type Command } from '../commands'

withDefaults(
  defineProps<{ commands: Command[]; activeIndex: number; placement?: 'above' | 'below' }>(),
  { placement: 'above' },
)
const emit = defineEmits<{ select: [command: Command]; close: [] }>()
</script>

<template>
  <!-- Anchored to the Composer Card (DESIGN.md — Command Palette). The rows
       share the text area's DOM order after it, so the listbox follows the
       textbox it belongs to; only the paint is lifted out of the card. The side
       is the caller's, because a popup that reaches past its scroll container's
       top edge is clipped by it, whatever its z-index. -->
  <div
    v-if="commands.length > 0"
    id="command-palette"
    role="listbox"
    aria-label="Commands"
    class="absolute left-0 z-20 max-h-64 w-full overflow-y-auto rounded-xl border border-line bg-paper-white p-1.5 shadow-elevated"
    :class="placement === 'below' ? 'top-full mt-2' : 'bottom-full mb-2'"
    @keydown.escape="emit('close')"
  >
    <button
      v-for="(command, index) in commands"
      :id="commandOptionId(command)"
      :key="command.id"
      type="button"
      role="option"
      :aria-selected="index === activeIndex"
      class="flex w-full cursor-pointer flex-col items-start rounded-lg px-3 py-2 text-left text-body-sm text-ink"
      :class="index === activeIndex ? 'bg-line/40' : 'hover:bg-line/40'"
      @mousedown.prevent
      @click="emit('select', command)"
    >
      <span class="font-medium">{{ command.label }}</span>
      <span class="text-subtext">{{ command.description }}</span>
    </button>
  </div>

  <p
    v-else
    id="command-palette"
    role="status"
    class="absolute left-0 z-20 w-full rounded-xl border border-line bg-paper-white px-3 py-2 text-body-sm text-subtext shadow-elevated"
    :class="placement === 'below' ? 'top-full mt-2' : 'bottom-full mb-2'"
  >
    No matching commands.
  </p>
</template>
