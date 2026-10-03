<script setup lang="ts">
import type { RouteLocationRaw } from 'vue-router'

/**
 * A link: text only, no fill and no border, darkening on hover. Not a button —
 * see DESIGN.md, Link.
 *
 * Renders a RouterLink when `to` is given, otherwise a button, because some
 * links are actions rather than navigation.
 *
 * `to` accepts a route location, not just a string, so callers can navigate by
 * name and survive the next path change.
 */
withDefaults(defineProps<{ to?: RouteLocationRaw; inline?: boolean }>(), {
  to: undefined,
  inline: false,
})

const emit = defineEmits<{ activate: [] }>()

const BASE =
  'rounded-sm text-body-sm text-tertiary transition-colors hover:text-ink focus-visible:ring-2 focus-visible:ring-ink focus-visible:ring-offset-2'
</script>

<template>
  <RouterLink v-if="to" :to="to" :class="[BASE, inline ? 'font-medium' : '']">
    <slot />
  </RouterLink>
  <button
    v-else
    type="button"
    :class="[BASE, inline ? 'font-medium' : '']"
    @click="emit('activate')"
  >
    <slot />
  </button>
</template>
