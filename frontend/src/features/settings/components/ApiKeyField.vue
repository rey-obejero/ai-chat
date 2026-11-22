<script setup lang="ts">
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { ref } from 'vue'

const apiKey = ref('')
</script>

<template>
  <div class="space-y-2">
    <InputText
      v-model="apiKey"
      type="password"
      placeholder="sk-…"
      aria-label="API key"
      class="w-full"
    />
    <div class="flex items-center gap-3">
      <Button label="Save key" size="small" disabled />
      <span class="text-body-sm text-subtext">Not wired up yet — keys are not stored.</span>
    </div>
  </div>
</template>
