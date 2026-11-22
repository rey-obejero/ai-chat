<script setup lang="ts">
import type { Component } from 'vue'

withDefaults(
  defineProps<{
    label: string
    icon: Component
    /** `filled` is the standing new-conversation row; `plain` the rest. */
    variant?: 'filled' | 'plain'
    active?: boolean
    collapsed?: boolean
  }>(),
  { variant: 'plain', active: false, collapsed: false },
)

const emit = defineEmits<{ select: [] }>()
</script>

<template>
  <button
    type="button"
    class="flex w-full cursor-pointer items-center rounded-lg px-2.5 py-2 text-left text-body-sm transition-colors motion-reduce:transition-none max-sm:justify-center"
    :class="[
      collapsed ? 'justify-center' : 'gap-2.5',
      variant === 'filled'
        ? 'bg-line/40 font-medium text-ink hover:bg-line/60'
        : active
          ? 'bg-line/60 font-medium text-ink'
          : 'text-ink hover:bg-line/40',
    ]"
    :aria-current="active ? 'true' : undefined"
    @click="emit('select')"
  >
    <component :is="icon" class="size-4 shrink-0 text-icon" stroke-width="2" />
    <!-- `sr-only` rather than `v-if`: hiding the label must not cost the
         button its accessible name. -->
    <span class="truncate" :class="collapsed ? 'sr-only' : ''">{{ label }}</span>
  </button>
</template>
