<script setup lang="ts">
import mark from '@/assets/logo.svg?raw'
</script>

<template>
  <span class="cursor-pointer inline-flex items-center text-onyx" role="img" aria-label="AI Chat">
    <span aria-hidden="true" class="h-[1.5em] shrink-0" v-html="mark" />
  </span>
</template>

<style scoped>
span :deep(svg) {
  display: block;
  width: auto;
  height: 100%;
}
</style>
