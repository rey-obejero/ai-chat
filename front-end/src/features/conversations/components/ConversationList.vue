<script setup lang="ts">
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
    <p v-if="loading" class="px-2.5 py-2 text-caption text-subtext" role="status">Loading…</p>
    <p v-else-if="error" class="px-2.5 py-2 text-caption text-subtext" role="alert">
      {{ error }}
    </p>
    <ul v-else class="space-y-0.5">
      <li v-for="conversation in conversations" :key="conversation.id">
        <button
          type="button"
          class="w-full cursor-pointer truncate rounded-lg px-2.5 py-2 text-left text-body-sm transition-colors motion-reduce:transition-none"
          :class="
            conversation.id === activeId
              ? 'bg-line/60 font-medium text-ink'
              : 'text-ink hover:bg-line/40'
          "
          :aria-current="conversation.id === activeId ? 'true' : undefined"
          @click="activeId = conversation.id"
        >
          {{ conversation.title }}
        </button>
      </li>
    </ul>
  </div>
</template>
