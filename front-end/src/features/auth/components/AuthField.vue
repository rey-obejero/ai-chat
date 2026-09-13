<script setup lang="ts">
defineProps<{
  label?: string
  htmlFor?: string
}>()
</script>

<template>
  <div class="space-y-1.5">
    <label v-if="label" :for="htmlFor" class="block text-sm font-medium text-ink">
      {{ label }}
    </label>
    <slot />
  </div>
</template>
