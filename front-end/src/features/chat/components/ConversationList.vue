<script setup lang="ts">
import type { Conversation } from '../stores/conversations'

defineProps<{
  conversations: Conversation[]
  loading: boolean
}>()
</script>

<template>
  <div class="space-y-1">
    <p v-if="loading" class="px-2 py-1 text-sm text-subtext">Loading…</p>
    <p v-else-if="conversations.length === 0" class="px-2 py-1 text-sm text-subtext">
      No conversations yet.
    </p>
    <button
      v-for="conversation in conversations"
      :key="conversation.id"
      type="button"
      class="w-full truncate rounded-lg px-2 py-1.5 text-left text-sm text-ink hover:bg-line"
    >
      {{ conversation.title }}
    </button>
  </div>
</template>
