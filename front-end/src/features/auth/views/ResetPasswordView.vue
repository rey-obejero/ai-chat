<script setup lang="ts">
import Button from 'primevue/button'
import Password from 'primevue/password'
import EmailPassword from 'supertokens-web-js/recipe/emailpassword'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import IconEye from '~icons/lucide/eye'
import IconEyeClosed from '~icons/lucide/eye-closed'
import IconLoaderCircle from '~icons/lucide/loader-circle'

import AppLink from '@/components/AppLink.vue'
import AuthField from '../components/AuthField.vue'
import AuthScreen from '../components/AuthScreen.vue'

/**
 * Read the token, then strip it from the address bar before anything else
 * runs. Left in place it would sit in the URL — and in browser history, and in
 * any `Referer` — until the form is submitted (ADR-0031).
 */
const token = EmailPassword.getResetPasswordTokenFromURL()

if (token) {
  const url = new URL(window.location.href)
  url.searchParams.delete('token')
  window.history.replaceState(window.history.state, '', `${url.pathname}${url.search}${url.hash}`)
}

const password = ref('')
const error = ref('')
const loading = ref(false)
const router = useRouter()

const hasToken = token !== ''

async function submit(): Promise<void> {
  error.value = ''
  loading.value = true
  try {
    const response = await EmailPassword.submitNewPassword({
      formFields: [{ id: 'password', value: password.value }],
      options: {
        // The SDK reads the token from the URL when this is called, but the URL
        // no longer carries it, so the captured value is put back into the
        // request body here. `tenantId` stays in the URL and needs no help.
        preAPIHook: async ({ url, requestInit }) => {
          const body = JSON.parse(String(requestInit.body ?? '{}'))
          body.token = token
          return { url, requestInit: { ...requestInit, body: JSON.stringify(body) } }
        },
      },
    })

    if (response.status === 'OK') {
      // A reset does not create a session, so the user signs in with the new
      // password rather than being dropped into the app.
      await router.replace({ name: 'sign-in', query: { reset: 'success' } })
    } else if (response.status === 'FIELD_ERROR') {
      error.value = response.formFields[0]?.error ?? 'Choose a stronger password.'
    } else {
      // Invalid, expired, or already used — tokens are single-use.
      error.value = 'This reset link is invalid or has expired.'
    }
  } catch {
    error.value = 'Something went wrong. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthScreen
    title="Set a new password"
    :intro="hasToken ? 'Choose a new password for your account' : undefined"
  >
    <div v-if="!hasToken" class="space-y-5">
      <p class="text-body text-ink" role="alert">
        This password reset link is missing its token, so it cannot be used.
      </p>
      <p class="text-center text-sm text-subtext">
        <AppLink :to="{ name: 'forgot-password' }" inline>Request a new link</AppLink>
      </p>
    </div>

    <form v-else class="space-y-5" @submit.prevent="submit">
      <AuthField>
        <Password
          input-id="password"
          v-model="password"
          :feedback="false"
          toggle-mask
          autocomplete="new-password"
          placeholder="Enter your new password"
          aria-label="New password"
          required
          fluid
        >
          <template #unmaskicon="{ toggleCallback }">
            <button
              type="button"
              aria-label="Show password"
              class="p-password-toggle-mask-icon p-password-unmask-icon flex !-mt-3 !size-6 cursor-pointer items-center justify-center rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink focus-visible:ring-offset-2"
              @click="toggleCallback"
            >
              <IconEyeClosed class="size-4" />
            </button>
          </template>
          <template #maskicon="{ toggleCallback }">
            <button
              type="button"
              aria-label="Hide password"
              class="p-password-toggle-mask-icon p-password-mask-icon flex !-mt-3 !size-6 cursor-pointer items-center justify-center rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink focus-visible:ring-offset-2"
              @click="toggleCallback"
            >
              <IconEye class="size-4" />
            </button>
          </template>
        </Password>
      </AuthField>

      <p v-if="error" class="text-sm font-medium text-danger" role="alert">
        {{ error }}
      </p>

      <p v-if="error" class="text-center text-sm text-subtext">
        <AppLink :to="{ name: 'forgot-password' }" inline>Request a new link</AppLink>
      </p>

      <Button
        type="submit"
        :label="loading ? undefined : 'Set new password'"
        :loading="loading"
        :aria-busy="loading"
        :aria-label="loading ? 'Saving' : undefined"
        class="w-full text-sm transition-opacity enabled:hover:!bg-ink enabled:hover:opacity-90"
      >
        <template #loadingicon>
          <IconLoaderCircle class="animate-spin" />
        </template>
      </Button>
    </form>
  </AuthScreen>
</template>
