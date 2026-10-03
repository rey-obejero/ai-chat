<script setup lang="ts">
import ProgressSpinner from 'primevue/progressspinner'
import ThirdParty from 'supertokens-web-js/recipe/thirdparty'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import AppLink from '@/components/AppLink.vue'

import AuthScreen from '../components/AuthScreen.vue'
import { useSessionStore } from '../stores/session'

const error = ref('')
const router = useRouter()
const session = useSessionStore()

onMounted(async () => {
  try {
    const response = await ThirdParty.signInAndUp()
    if (response.status === 'OK') {
      await session.refresh()
      await router.replace({ name: 'conversations' })
    } else {
      error.value = 'Your provider did not share an email address.'
    }
  } catch {
    error.value = 'Social sign-in failed. Please try again.'
  }
})
</script>

<template>
  <AuthScreen title="Signing you in.">
    <div class="flex flex-col items-center gap-4">
      <div class="flex items-center gap-3 text-subtext">
        <ProgressSpinner
          v-if="!error"
          :style="{ width: '1.25rem', height: '1.25rem' }"
          stroke-width="6"
          class="motion-reduce:hidden"
          aria-label="Signing in"
        />
        <p class="text-sm">{{ error || 'Completing sign-in…' }}</p>
      </div>
      <AppLink v-if="error" :to="{ name: 'sign-in' }" inline>Back to sign in</AppLink>
    </div>
  </AuthScreen>
</template>
