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

    <p v-if="loading" class="px-3 py-1.5 text-body-sm text-subtext">Loading…</p>
    <p v-else-if="error" class="px-3 py-1.5 text-body-sm text-subtext">{{ error }}</p>
    <p v-else-if="conversations.length === 0" class="px-3 py-1.5 text-body-sm text-subtext">
      No conversations yet.
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
