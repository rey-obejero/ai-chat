<script setup lang="ts">
import BrandLogo from '@/components/BrandLogo.vue'

defineProps<{
  title: string
  intro?: string
}>()
</script>

<template>
  <main class="flex min-h-screen flex-col bg-canvas px-6 pt-6 text-ink sm:px-9 sm:pt-7">
    <header class="flex items-center">
      <BrandLogo class="text-xl sm:text-2xl" />
    </header>

    <div class="flex flex-1 items-center justify-center py-10">
      <section class="w-full max-w-md" aria-labelledby="auth-title">
        <header class="text-center">
          <h1 id="auth-title" class="text-heading font-semibold sm:text-heading-lg">
            {{ title }}
          </h1>
          <p v-if="intro" class="mt-3 text-body text-subtext">
            {{ intro }}
          </p>
        </header>
        <div class="mt-8">
          <slot />
        </div>
      </section>
    </div>
  </main>
</template>
