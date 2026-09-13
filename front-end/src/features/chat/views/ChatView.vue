<script setup lang="ts">
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { useSessionStore } from '@/features/auth'
import ConversationList from '../components/ConversationList.vue'
import { useConversationsStore } from '../stores/conversations'

const session = useSessionStore()
const conversations = useConversationsStore()
const router = useRouter()

onMounted(() => {
  void conversations.load()
})

async function signOut(): Promise<void> {
  await session.signOut()
  await router.replace('/sign-in')
}
</script>

<template>
  <div class="flex h-screen bg-canvas text-ink">
    <aside class="flex w-64 flex-col border-r border-line bg-paper-white">
      <div class="flex items-center justify-between px-4 py-4">
        <span class="annotation text-ink">AI Chat</span>
        <Button
          type="button"
          label="New"
          size="small"
          severity="secondary"
          outlined
          aria-label="New conversation"
        />
      </div>
      <nav class="flex-1 overflow-y-auto px-2">
        <ConversationList
          :conversations="conversations.conversations"
          :loading="conversations.loading"
        />
      </nav>
      <div class="border-t border-line p-3">
        <p class="truncate text-xs text-subtext">{{ session.user?.email }}</p>
        <Button
          type="button"
          label="Sign out"
          link
          size="small"
          class="mt-1 px-0"
          @click="signOut"
        />
      </div>
    </aside>

    <main class="flex flex-1 flex-col">
      <header class="border-b border-line px-6 py-4">
        <h1 class="text-heading-sm font-semibold">Chat</h1>
      </header>

      <section class="flex flex-1 items-center justify-center px-6 text-center">
        <div>
          <h2 class="text-heading font-semibold">Ask anything</h2>
          <p class="mt-2 text-sm text-subtext">
            Streaming replies, retrieval, and tools land here next.
          </p>
        </div>
      </section>

      <footer class="border-t border-line p-4">
        <div class="flex gap-2">
          <InputText
            disabled
            placeholder="Messaging is coming soon…"
            class="flex-1"
            aria-label="Message"
          />
          <Button type="button" label="Send" disabled />
        </div>
      </footer>
    </main>
  </div>
</template>
