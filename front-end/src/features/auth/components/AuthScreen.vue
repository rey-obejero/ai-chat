<script setup lang="ts">
defineProps<{
  title: string
  intro?: string
}>()
</script>

<template>
  <main
    class="flex min-h-screen items-center justify-center bg-canvas px-4 py-10 text-ink sm:px-6 sm:py-14"
  >
    <section
      class="w-full max-w-md rounded-xl border border-line bg-paper-white p-5 shadow-subtle-2 sm:p-8"
      aria-labelledby="auth-title"
    >
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
