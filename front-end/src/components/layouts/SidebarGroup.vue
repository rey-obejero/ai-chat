<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import IconChevronRight from '~icons/lucide/chevron-right'

const props = defineProps<{ title: string; storageKey: string }>()

const expanded = ref(localStorage.getItem(`sidebar-group-${props.storageKey}`) !== 'false')

const chevron = computed(() =>
  expanded.value
    ? 'rotate-90 transition-transform motion-reduce:transition-none'
    : 'transition-transform motion-reduce:transition-none',
)

function toggle(): void {
  expanded.value = !expanded.value
}

watch(expanded, (value) => {
  localStorage.setItem(`sidebar-group-${props.storageKey}`, String(value))
})

defineExpose({ expanded })
</script>

<template>
  <section class="group mt-5">
    <!-- A button, not a heading: the global h1–h3 weight rule would otherwise
         force 600 onto what is a quiet label. -->
    <button
      type="button"
      class="flex w-full cursor-pointer items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-left text-body-sm text-subtext transition-colors hover:text-ink motion-reduce:transition-none"
      :aria-expanded="expanded"
      @click="toggle"
    >
      <span class="truncate">{{ title }}</span>
      <IconChevronRight
        class="size-3 shrink-0 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100 motion-reduce:transition-none"
        :class="chevron"
        stroke-width="2"
      />
    </button>

    <div v-show="expanded" class="mt-0.5 space-y-0.5">
      <slot />
    </div>
  </section>
</template>
