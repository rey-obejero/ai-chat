<script setup lang="ts">
defineProps<{
  title: string
  intro?: string
}>()
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-canvas px-5 py-14 text-ink">
    <section class="w-full max-w-md" aria-labelledby="auth-title">
      <header class="text-center">
        <h1 id="auth-title" class="text-heading font-semibold sm:text-heading-lg">
          {{ title }}
        </h1>
        <p v-if="intro" class="mt-2 text-body-sm text-subtext sm:text-body">
          {{ intro }}
        </p>
      </header>
      <div class="mt-8">
        <slot />
      </div>
    </section>
  </main>
</template>
