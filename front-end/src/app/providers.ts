import PrimeVue from 'primevue/config'
import ConfirmationService from 'primevue/confirmationservice'
import Tooltip from 'primevue/tooltip'
import { createPinia } from 'pinia'
import SuperTokens from 'supertokens-web-js'
import EmailPassword from 'supertokens-web-js/recipe/emailpassword'
import Session from 'supertokens-web-js/recipe/session'
import ThirdParty from 'supertokens-web-js/recipe/thirdparty'
import type { App } from 'vue'

import { AiChatPreset } from './theme'

export function setupSuperTokens(): void {
  SuperTokens.init({
    appInfo: {
      appName: 'AI Chat',
      apiDomain: window.location.origin,
      apiBasePath: '/api/auth',
    },
    recipeList: [Session.init(), EmailPassword.init(), ThirdParty.init()],
  })
}

export function installProviders(app: App): void {
  app.use(createPinia())
  app.directive('tooltip', Tooltip)
  // The delete confirmation is the only thing that asks for it (ConversationsView).
  app.use(ConfirmationService)
  app.use(PrimeVue, {
    theme: {
      preset: AiChatPreset,
      options: {
        darkModeSelector: '.app-dark',
      },
    },
    ripple: false,
  })
}
