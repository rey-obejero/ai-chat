<script setup lang="ts">
import AppLink from '@/components/AppLink.vue'
import BrandLogo from '@/components/BrandLogo.vue'

/**
 * The session check failed, so the app cannot tell whether the visitor is
 * signed in. Saying "signed out" would invite a sign-in that cannot succeed;
 * this screen offers a retry, which re-runs the check from the start.
 */
function retry(): void {
  window.location.reload()
}
</script>

<template>
  <main
    class="flex min-h-screen flex-col items-center justify-center gap-6 bg-canvas px-6 text-ink"
  >
    <BrandLogo class="text-xl" />
    <div class="text-center">
      <h1 class="text-heading-lg font-semibold">Service unavailable</h1>
      <p class="mt-3 text-body text-subtext">
        We could not confirm your session right now. Check your connection and try again in a
        moment.
      </p>
    </div>
    <AppLink @activate="retry">Try again</AppLink>
  </main>
</template>
