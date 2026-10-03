<script setup lang="ts">
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import EmailPassword from 'supertokens-web-js/recipe/emailpassword'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

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

async function submit(): Promise<void> {
  error.value = ''
  loading.value = true
  try {
    const response = await EmailPassword.signUp({
      formFields: [
        { id: 'email', value: email.value },
        { id: 'password', value: password.value },
      ],
    })

    if (response.status === 'OK') {
      await session.refresh()
      // Honour the same redirect intent as sign-in, so a user who
      // deep-linked and then registered still lands where they meant to.
      await router.push(safeRedirect(route.query.redirectTo, { name: 'conversations' }))
    } else if (response.status === 'FIELD_ERROR') {
      error.value = response.formFields[0]?.error ?? 'Could not create your account.'
    } else {
      error.value = 'Could not create your account.'
    }
  } catch {
    error.value = 'Something went wrong. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthScreen title="Sign up" intro="Create an account to get started">
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
          autocomplete="new-password"
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

      <SocialButtons />

      <p class="text-center text-sm text-subtext">
        Already have an account?
        <AppLink :to="{ name: 'sign-in' }" inline>Sign in</AppLink>
      </p>
    </form>
  </AuthScreen>
</template>
