<script setup lang="ts">
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import EmailPassword from 'supertokens-web-js/recipe/emailpassword'
import { ref } from 'vue'
import { useRoute, useRouter, type RouteLocationRaw } from 'vue-router'

import IconEye from '~icons/lucide/eye'
import IconEyeClosed from '~icons/lucide/eye-closed'
import IconLoaderCircle from '~icons/lucide/loader-circle'

import AppLink from '@/components/AppLink.vue'
import { safeRedirect } from '@/lib/redirect'
import AuthField from '../components/AuthField.vue'
import AuthScreen from '../components/AuthScreen.vue'
import SocialButtons from '../components/SocialButtons.vue'
import { useSessionStore } from '../stores/session'

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const route = useRoute()
const router = useRouter()
const session = useSessionStore()

// `redirectTo` comes from the query string, so it is validated rather than
// trusted: a protocol-relative value would send the user off-origin.
function redirectTarget(): RouteLocationRaw {
  return safeRedirect(route.query.redirectTo, { name: 'conversations' })
}

async function submit(): Promise<void> {
  error.value = ''
  loading.value = true
  try {
    const response = await EmailPassword.signIn({
      formFields: [
        { id: 'email', value: email.value },
        { id: 'password', value: password.value },
      ],
    })

    if (response.status === 'OK') {
      await session.refresh()
      // `push`, not `replace`: keeping sign-in in history makes the back
      // button after signing in behave predictably.
      await router.push(redirectTarget())
    } else if (response.status === 'FIELD_ERROR') {
      error.value = response.formFields[0]?.error ?? 'Check your email and password.'
    } else {
      error.value = 'That email and password do not match.'
    }
  } catch {
    error.value = 'Something went wrong. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthScreen title="Sign in" intro="Enter your credentials to access your account">
    <form class="space-y-5" @submit.prevent="submit">
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

      <AuthField>
        <Password
          input-id="password"
          v-model="password"
          :feedback="false"
          toggle-mask
          autocomplete="current-password"
          placeholder="Enter your password"
          aria-label="Password"
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
        <div class="flex justify-end pt-1">
          <AppLink class="py-1">Forgot password?</AppLink>
        </div>
      </AuthField>

      <p v-if="error" class="text-sm font-medium text-danger" role="alert">
        {{ error }}
      </p>

      <Button
        type="submit"
        :label="loading ? undefined : 'Continue'"
        :loading="loading"
        :aria-busy="loading"
        :aria-label="loading ? 'Continuing' : undefined"
        class="w-full text-sm transition-opacity enabled:hover:!bg-ink enabled:hover:opacity-90"
      >
        <template #loadingicon>
          <IconLoaderCircle class="animate-spin" />
        </template>
      </Button>

      <p class="text-center text-xs font-medium uppercase tracking-wide text-subtext">or</p>

      <SocialButtons />

      <p class="text-center text-sm text-subtext">
        Don't have an account?
        <AppLink :to="{ name: 'sign-up' }" inline>Sign up</AppLink>
      </p>
    </form>
  </AuthScreen>
</template>
