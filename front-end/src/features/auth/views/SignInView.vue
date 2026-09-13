<script setup lang="ts">
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import EmailPassword from 'supertokens-web-js/recipe/emailpassword'
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import IconCircleAlert from '~icons/lucide/circle-alert'

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

function redirectTarget(): string {
  return typeof route.query.redirect === 'string' ? route.query.redirect : '/chat'
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
      await router.replace(redirectTarget())
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
  <AuthScreen title="Sign In" intro="Enter your credentials to continue.">
    <form class="space-y-5" @submit.prevent="submit">
      <AuthField label="Email" html-for="email">
        <InputText
          id="email"
          v-model="email"
          type="email"
          autocomplete="email"
          placeholder="name@company.com"
          required
          class="w-full"
        />
      </AuthField>

      <AuthField label="Password" html-for="password">
        <Password
          input-id="password"
          v-model="password"
          :feedback="false"
          toggle-mask
          autocomplete="current-password"
          placeholder="••••••••"
          required
          fluid
        />
      </AuthField>

      <div class="flex justify-end">
        <Button type="button" link size="small" label="Forgot password?" class="px-0" />
      </div>

      <p v-if="error" class="flex items-center gap-1.5 text-sm font-medium text-ink" role="alert">
        <IconCircleAlert class="shrink-0 text-icon" />
        {{ error }}
      </p>

      <Button type="submit" label="Sign in" :loading="loading" class="w-full" />

      <div class="flex items-center gap-3">
        <span class="h-px flex-1 bg-line" />
        <span class="text-xs text-subtext">or</span>
        <span class="h-px flex-1 bg-line" />
      </div>

      <SocialButtons />

      <p class="text-center text-sm text-subtext">
        New here?
        <RouterLink to="/sign-up" class="text-ink underline underline-offset-4 hover:text-subtext">
          Create an account
        </RouterLink>
      </p>
    </form>
  </AuthScreen>
</template>
