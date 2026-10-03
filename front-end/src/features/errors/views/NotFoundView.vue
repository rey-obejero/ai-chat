<script setup lang="ts">
import { RouterLink } from 'vue-router'

import BrandLogo from '@/components/BrandLogo.vue'
</script>

<template>
  <main
    class="flex min-h-screen flex-col items-center justify-center gap-6 bg-canvas px-6 text-ink"
  >
    <BrandLogo class="text-xl" />
    <div class="text-center">
      <h1 class="text-heading-lg font-semibold">Page not found</h1>
      <p class="mt-3 text-body text-subtext">
        That address does not match anything in the application.
      </p>
    </div>
    <RouterLink
      :to="{ name: 'conversations' }"
      class="rounded-sm text-body-sm font-medium text-tertiary transition-colors hover:text-ink focus-visible:ring-2 focus-visible:ring-ink focus-visible:ring-offset-2"
    >
      Go to conversations
    </RouterLink>
  </main>
</template>
