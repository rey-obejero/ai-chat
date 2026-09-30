<script setup lang="ts"></script>

<template>
  <header class="flex h-14 shrink-0 items-center justify-between gap-4 px-6">
    <div class="min-w-0 truncate text-body-sm text-subtext">
      <slot name="title" />
    </div>
    <div class="flex shrink-0 items-center gap-2">
      <slot name="actions" />
    </div>
  </header>
</template>
