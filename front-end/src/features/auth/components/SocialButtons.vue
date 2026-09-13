<script setup lang="ts">
import Button from 'primevue/button'
import ThirdParty from 'supertokens-web-js/recipe/thirdparty'
import { ref } from 'vue'

import IconCircleAlert from '~icons/lucide/circle-alert'
import IconGithub from '~icons/tabler/brand-github'
import IconGoogle from '~icons/tabler/brand-google'

const error = ref('')
const pending = ref<'google' | 'github' | null>(null)

async function signInWith(thirdPartyId: 'google' | 'github'): Promise<void> {
  error.value = ''
  pending.value = thirdPartyId
  try {
    const url = await ThirdParty.getAuthorisationURLWithQueryParamsAndSetState({
      thirdPartyId,
      frontendRedirectURI: `${window.location.origin}/auth/callback`,
    })
    window.location.assign(url)
  } catch {
    error.value = 'Social sign-in is unavailable right now.'
    pending.value = null
  }
}
</script>

<template>
  <div class="space-y-3">
    <div class="flex flex-col gap-3">
      <Button
        type="button"
        severity="secondary"
        outlined
        class="justify-center text-sm"
        :loading="pending === 'google'"
        @click="signInWith('google')"
      >
        <IconGoogle class="mr-2 text-base" />
        Continue with Google
      </Button>
      <Button
        type="button"
        severity="secondary"
        outlined
        class="justify-center text-sm"
        :loading="pending === 'github'"
        @click="signInWith('github')"
      >
        <IconGithub class="mr-2 text-base" />
        Continue with GitHub
      </Button>
    </div>
    <p
      v-if="error"
      class="flex items-center justify-center gap-1.5 text-sm font-medium text-ink"
      role="alert"
    >
      <IconCircleAlert class="shrink-0 text-icon" />
      {{ error }}
    </p>
  </div>
</template>
