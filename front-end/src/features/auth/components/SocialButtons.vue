<script setup lang="ts">
import Button from 'primevue/button'
import ThirdParty from 'supertokens-web-js/recipe/thirdparty'
import { computed, onMounted, ref, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import IconGithub from '~icons/logos/github-icon'
import IconGoogle from '~icons/logos/google-icon'

import { listSocialProviders, type SocialProvider } from '../api'

/**
 * Brand artwork, by provider id.
 *
 * Only providers we have a real mark for appear here. Anything else renders as
 * a plain button carrying its name — a stand-in icon for an unknown brand would
 * be inventing branding we do not have.
 */
const ICONS: Record<string, Component> = {
  google: IconGoogle,
  github: IconGithub,
}

const route = useRoute()
const router = useRouter()

const available = ref<SocialProvider[]>([])
const error = ref('')
const pending = ref<string | null>(null)

// Providers are configured per deployment, so the list comes from the API
// rather than being hardcoded — ADR-0010 already decided this, and the code was
// contradicting it by rendering buttons for unconfigured providers.
const buttons = computed(() =>
  available.value.map((provider) => ({ ...provider, icon: ICONS[provider.id] })),
)

onMounted(async () => {
  try {
    available.value = await listSocialProviders()
  } catch {
    error.value = 'Social sign-in is unavailable right now.'
  }
})

/**
 * Where SuperTokens should send the browser once the provider is done.
 *
 * `redirectTo` is carried across the round trip as a query parameter on this
 * URL — the user leaves the site entirely, so in-page state does not survive.
 * It is re-validated on arrival by the callback view, because a value that
 * round-trips through a URL is user-controllable.
 */
function callbackUrl(): URL {
  const url = new URL(router.resolve({ name: 'auth-callback' }).href, window.location.origin)
  const redirectTo = route.query.redirectTo
  if (typeof redirectTo === 'string' && redirectTo.length > 0) {
    url.searchParams.set('redirectTo', redirectTo)
  }
  return url
}

async function signInWith(thirdPartyId: string): Promise<void> {
  if (pending.value) return
  error.value = ''
  pending.value = thirdPartyId
  try {
    const url = await ThirdParty.getAuthorisationURLWithQueryParamsAndSetState({
      thirdPartyId,
      // `shouldTryLinkingWithSessionUser` is deliberately never passed. Leaving
      // it undefined means the SDK attempts no account linking, so a social
      // sign-in is refused rather than merged when the address already exists
      // — see ADR-0028. Passing it, or setting it to true, would silently
      // reintroduce auto-linking.
      // Resolved from the router rather than concatenated, so renaming the
      // route cannot silently desync this from where the view is mounted. This
      // is *not* the URI registered with the provider: that one is
      // SuperTokens' own `/api/auth/callback/{provider}`, handled in its
      // backend before it forwards the browser here.
      frontendRedirectURI: callbackUrl().toString(),
    })
    window.location.assign(url)
  } catch {
    error.value = 'Social sign-in is unavailable right now.'
    pending.value = null
  }
}
</script>

<template>
  <!-- The divider lives here, not in the sign-in and sign-up views, so that one
       condition governs it and the buttons together. With them apart, hiding
       the buttons left an "or" separating the form from nothing — which is the
       tell of a hardcoded list.
       Rendered when there is a button to show *or* something went wrong: on a
       failed lookup there are no buttons, and hiding the message then would
       leave the user with no idea why. -->
  <div v-if="buttons.length > 0 || error" class="space-y-3">
    <template v-if="buttons.length > 0">
      <p class="text-center text-xs font-medium uppercase tracking-wide text-subtext">or</p>
      <div class="flex flex-col gap-3">
        <Button
          v-for="provider in buttons"
          :key="provider.id"
          type="button"
          severity="secondary"
          outlined
          class="justify-center text-sm"
          :loading="pending === provider.id"
          :disabled="pending !== null"
          @click="signInWith(provider.id)"
        >
          <component :is="provider.icon" v-if="provider.icon" class="mr-2 text-base" />
          Continue with {{ provider.name }}
        </Button>
      </div>
    </template>
    <p v-if="error" class="text-center text-sm font-medium text-danger" role="alert">
      {{ error }}
    </p>
  </div>
</template>
