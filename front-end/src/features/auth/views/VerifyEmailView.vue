<script setup lang="ts">
import EmailVerification from 'supertokens-web-js/recipe/emailverification'
import { computed, onMounted, ref } from 'vue'

import AppLink from '@/components/AppLink.vue'
import AuthScreen from '../components/AuthScreen.vue'
import VerificationResend from '../components/VerificationResend.vue'

/**
 * The states the emailed link can land in: the recipe is still answering, the
 * token was accepted, it was refused (expired, or already used — the tokens are
 * single-use), or the request itself did not come back. A refusal and a failure
 * are not the same claim, so they do not share copy.
 */
type VerificationState = 'verifying' | 'verified' | 'expired' | 'failed'

const state = ref<VerificationState>('verifying')

const title = computed(() => (state.value === 'verified' ? 'Email verified' : 'Verify your email'))

/**
 * Read the token, then strip it from the address bar before anything else runs.
 * Left in place it would sit in the URL — and in browser history, and in any
 * `Referer` — for the life of the page (ADR-0031).
 */
const token = EmailVerification.getEmailVerificationTokenFromURL()

if (token) {
  const url = new URL(window.location.href)
  url.searchParams.delete('token')
  const stripped = `${url.pathname}${url.search}${url.hash}`
  // vue-router keeps its own copy of this entry in `history.state` and writes it
  // back into the address bar on the next navigation, so the stripped URL has to
  // replace that too: otherwise the token returns with the next push and stays on
  // the entry behind it (ADR-0031).
  window.history.replaceState({ ...window.history.state, current: stripped }, '', stripped)
}

/**
 * The link is the whole point of the route, so it is followed on load rather
 * than behind a button. `tenantId` stays in the URL for the recipe to read; the
 * token is re-injected into the request body here, because the SDK reads it
 * from a URL that no longer carries it.
 */
async function verify(): Promise<void> {
  try {
    const response = await EmailVerification.verifyEmail({
      options: {
        preAPIHook: async ({ url, requestInit }) => {
          const body = JSON.parse(String(requestInit.body ?? '{}'))
          body.token = token
          return { url, requestInit: { ...requestInit, body: JSON.stringify(body) } }
        },
      },
    })

    state.value = response.status === 'OK' ? 'verified' : 'expired'
  } catch {
    state.value = 'failed'
  }
}

onMounted(() => void verify())
</script>

<template>
  <AuthScreen :title="title">
    <div class="space-y-5">
      <p v-if="state === 'verifying'" role="status" class="text-center text-body text-subtext">
        Verifying your email address…
      </p>

      <template v-else-if="state === 'verified'">
        <p role="status" class="text-center text-body text-ink">
          Your email address is verified. Your account now has the full token allowance.
        </p>
        <p class="text-center text-sm text-subtext">
          <AppLink :to="{ name: 'conversations' }" inline>Go to AI Chat</AppLink>
        </p>
      </template>

      <template v-else>
        <p v-if="state === 'expired'" role="alert" class="text-center text-body text-danger">
          This verification link is invalid or has expired.
        </p>
        <p v-else role="alert" class="text-center text-body text-danger">
          Something went wrong. Please try again.
        </p>

        <VerificationResend />

        <p class="text-center text-sm text-subtext">
          <AppLink :to="{ name: 'sign-in' }" inline>Back to sign in</AppLink>
        </p>
      </template>
    </div>
  </AuthScreen>
</template>
