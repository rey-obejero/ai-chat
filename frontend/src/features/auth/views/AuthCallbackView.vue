<script setup lang="ts">
import ProgressSpinner from 'primevue/progressspinner'
import ThirdParty from 'supertokens-web-js/recipe/thirdparty'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import AppLink from '@/components/AppLink.vue'
import { safeRedirect, takeRedirect } from '@/lib/redirect'

import AuthScreen from '../components/AuthScreen.vue'
import { useSessionStore } from '../stores/session'

/**
 * Copy is keyed off `status`, never off the provider's `reason`. The reason
 * originates at the provider, so its wording is not ours to control and it may
 * echo user input — it gets logged, not rendered.
 */
const COPY = {
  existingAccount:
    'That address already has an account. Sign in with your email and password instead.',
  noEmail: 'This provider did not share an email address, so it cannot be used to sign in here.',
  provider: 'Your provider could not complete the sign-in. Please try again.',
} as const

type Failure = keyof typeof COPY

const error = ref<Failure | ''>('')
const router = useRouter()
const session = useSessionStore()

// The destination was stored in the tab before the browser left for the
// provider (the callback URL itself must carry no query — see SocialButtons).
// Reading it here also clears it, and it is validated because it is still
// user-controllable at the point it was stored.
const rememberedRedirect = takeRedirect()
const redirectTarget = safeRedirect(rememberedRedirect, { name: 'conversations' })

const signInLink = computed(() => ({
  name: 'sign-in',
  query: rememberedRedirect ? { redirectTo: rememberedRedirect } : {},
}))

onMounted(async () => {
  try {
    const response = await ThirdParty.signInAndUp()

    if (response.status === 'OK') {
      await session.refresh()
      await router.replace(redirectTarget)
      return
    }

    if (response.status === 'SIGN_IN_UP_NOT_ALLOWED') {
      // The common case by far: account linking is refused, so the user has to
      // return to password sign-in. The reason string is for the log only.
      console.warn('social sign-in refused', response.reason)
      error.value = 'existingAccount'
      return
    }

    if (response.status === 'NO_EMAIL_GIVEN_BY_PROVIDER') {
      error.value = 'noEmail'
      return
    }

    error.value = 'provider'
  } catch (cause) {
    console.warn('social sign-in failed', cause)
    error.value = 'provider'
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
        <p class="text-sm">{{ error ? COPY[error] : 'Completing sign-in…' }}</p>
      </div>
      <AppLink v-if="error" :to="signInLink" inline>Back to sign in</AppLink>
    </div>
  </AuthScreen>
</template>
