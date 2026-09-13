import { createApp } from 'vue'

import App from './App.vue'
import { installProviders, setupSuperTokens } from './app/providers'
import { router } from './app/router'
import './assets/main.css'

setupSuperTokens()

const app = createApp(App)
installProviders(app)
app.use(router)
app.mount('#app')
