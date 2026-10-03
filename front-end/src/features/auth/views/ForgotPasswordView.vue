<script setup lang="ts">
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import EmailPassword from 'supertokens-web-js/recipe/emailpassword'
import { ref } from 'vue'

import IconLoaderCircle from '~icons/lucide/loader-circle'

import AppLink from '@/components/AppLink.vue'
import AuthField from '../components/AuthField.vue'
import AuthScreen from '../components/AuthScreen.vue'

const email = ref('')
const error = ref('')
const loading = ref(false)
const submitted = ref(false)

/**
 * One confirmation for every outcome that is not a malformed address.
 *
 * The server answers identically for a known and an unknown account, and this
 * copy must not imply otherwise — "we sent you an email" asserts a fact the
 * server deliberately declines to confirm. `PASSWORD_RESET_NOT_ALLOWED`
 * collapses into the same view, because it too would reveal something about
 * the account (ADR-0031).
 */
async function submit(): Promise<void> {
  error.value = ''
  loading.value = true
  try {
    const response = await EmailPassword.sendPasswordResetEmail({
      formFields: [{ id: 'email', value: email.value }],
    })

    if (response.status === 'FIELD_ERROR') {
      error.value = response.formFields[0]?.error ?? 'Enter a valid email address.'
    } else {
      submitted.value = true
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
    title="Reset your password"
    intro="Enter your email and we'll send you a link to set a new password"
  >
    <div v-if="submitted" class="space-y-5">
      <p class="text-body text-ink" role="status">
        If that address has an account, we've sent a link to reset your password.
      </p>
      <p class="text-center text-sm text-subtext">
        <AppLink :to="{ name: 'sign-in' }" inline>Back to sign in</AppLink>
      </p>
    </div>

    <form v-else class="space-y-5" @submit.prevent="submit">
      <AuthField>
        <InputText
          id="email"
          v-model="email"
          type="email"
          autocomplete="email"
          placeholder="Enter your email"
          aria-label="Email"
          required
          class="w-full"
        />
      </AuthField>

      <p v-if="error" class="text-sm font-medium text-danger" role="alert">
        {{ error }}
      </p>

      <Button
        type="submit"
        :label="loading ? undefined : 'Send reset link'"
        :loading="loading"
        :aria-busy="loading"
        :aria-label="loading ? 'Sending' : undefined"
        class="w-full text-sm transition-opacity enabled:hover:!bg-ink enabled:hover:opacity-90"
      >
        <template #loadingicon>
          <IconLoaderCircle class="animate-spin" />
        </template>
      </Button>

      <p class="text-center text-sm text-subtext">
        <AppLink :to="{ name: 'sign-in' }" inline>Back to sign in</AppLink>
      </p>
    </form>
  </AuthScreen>
</template>
