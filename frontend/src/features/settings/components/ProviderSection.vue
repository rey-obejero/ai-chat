<script setup lang="ts">
import RadioButton from 'primevue/radiobutton'
import { ref } from 'vue'

import ApiKeyField from './ApiKeyField.vue'

// Local UI state only: the choice is not persisted and BYOK is not wired up
// (ADR-0019). The server-provided model is the default.
const provider = ref<'server' | 'byok'>('server')
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-start gap-3">
      <RadioButton v-model="provider" input-id="provider-server" value="server" />
      <div>
        <label for="provider-server" class="block text-body-sm font-medium text-ink">
          AI Chat (server-provided)
        </label>
        <p class="text-body-sm text-subtext">Use the model this server is configured with.</p>
      </div>
    </div>

    <div class="flex items-start gap-3">
      <RadioButton v-model="provider" input-id="provider-byok" value="byok" />
      <div class="flex-1">
        <label for="provider-byok" class="block text-body-sm font-medium text-ink">
          Your own API key
        </label>
        <p class="text-body-sm text-subtext">
          Send requests with a key you control; usage is billed to your provider account.
        </p>
        <ApiKeyField v-if="provider === 'byok'" class="mt-3" />
      </div>
    </div>
  </div>
</template>
