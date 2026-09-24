<script setup lang="ts">
import Listbox from 'primevue/listbox'

import type { Conversation } from '../stores/conversations'

const activeId = defineModel<string | null>('activeId')

defineProps<{
  conversations: Conversation[]
  loading: boolean
  error?: string
}>()
</script>

<template>
  <div>
    <p class="px-3 pb-1 pt-2 text-caption text-subtext">Conversations</p>

    <p v-if="loading" class="px-3 py-2 text-body-sm text-subtext" role="status">Loading…</p>
    <p v-else-if="error" class="px-3 py-2 text-body-sm text-subtext" role="alert">{{ error }}</p>
    <p v-else-if="conversations.length === 0" class="px-3 py-2 text-body-sm text-subtext">
      No conversations yet. Start one above.
    </p>
    <Listbox
      v-else
      v-model="activeId"
      :options="conversations"
      option-label="title"
      option-value="id"
      class="w-full"
    />
  </div>
</template>
