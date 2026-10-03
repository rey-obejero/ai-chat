<script setup lang="ts">
import { useChat } from '@ai-sdk/vue'
import Avatar from 'primevue/avatar'
import Menu from 'primevue/menu'
import type { MenuItem } from 'primevue/menuitem'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import RootLayout from '@/components/layouts/RootLayout.vue'
import SidebarGroup from '@/components/layouts/SidebarGroup.vue'
import { useSessionStore } from '@/features/auth'
import { SettingsDialog } from '@/features/settings'
import { listMessages } from '../api'
import ConversationList from '../components/ConversationList.vue'
import MessageComposer from '../components/MessageComposer.vue'
import MessageList from '../components/MessageList.vue'
import SuggestionChips from '../components/SuggestionChips.vue'
import { createConversationTransport, describeError, toUIMessages } from '../messages'
import { useConversationsStore } from '../stores/conversations'

const session = useSessionStore()
const conversations = useConversationsStore()
const route = useRoute()
const router = useRouter()

const collapsed = ref(localStorage.getItem('sidebar-collapsed') === 'true')
const draft = ref('')
const accountMenu = ref()
const settingsOpen = ref(false)
const composer = ref<InstanceType<typeof MessageComposer> | null>(null)
const scrollArea = ref<HTMLElement | null>(null)
const hydrating = ref(false)

const conversationId = computed(() => {
  const id = route.params.id
  return typeof id === 'string' && id.length > 0 ? id : null
})

const title = computed(
  () => conversations.conversations.find((item) => item.id === conversationId.value)?.title ?? '',
)

const chat = useChat({
  transport: createConversationTransport(() => conversationId.value),
  // The server names a conversation from its first message, so the sidebar
  // needs a refresh once a reply completes.
  onFinish: () => {
    void conversations.load()
  },
})

// `chat.messages` is mutated in place, so handing a fresh copy to the child is
// what makes the message list re-render at all.
const messages = computed(() => [...chat.messages.value])
const busy = computed(() => {
  const value = chat.status.value
  return value !== 'ready' && value !== 'error'
})
// `submitted` is the window between sending and the first token arriving, when
// there is nothing in the list yet to show for the request.
const working = computed(() => chat.status.value === 'submitted')
const errorMessage = computed(() => (chat.error.value ? describeError(chat.error.value) : ''))
const canSend = computed(() => draft.value.trim().length > 0 && !busy.value && !hydrating.value)

const activeId = computed({
  get: () => conversationId.value,
  set: (id: string | null) => {
    if (id) void router.push({ name: 'conversations', params: { id } })
  },
})

const initial = computed(() => (session.user?.email ?? '?').charAt(0).toUpperCase())

const accountItems = computed<MenuItem[]>(() => [
  { label: 'Personalization' },
  { label: 'Profile' },
  { label: 'Settings', command: () => (settingsOpen.value = true) },
  { separator: true },
  { label: 'Sign out', command: () => void signOut() },
])

watch(collapsed, (value) => {
  localStorage.setItem('sidebar-collapsed', String(value))
})

// Follow the newest turn, including while it streams in.
watch(messages, () => void scrollToNewest(), { flush: 'post' })

onMounted(() => {
  void conversations.load()
})

// One watcher covers both entry paths: selecting a conversation, and arriving
// at a freshly created one with a message already queued. Hydration must
// finish before a send is allowed, or the fetched history would overwrite the
// optimistic user message and the incoming stream.
watch(
  conversationId,
  async (id) => {
    if (!id) {
      chat.messages.value = []
      await focusComposer()
      return
    }

    hydrating.value = true
    try {
      const history = await listMessages(id)
      if (conversationId.value === id) {
        chat.messages.value = toUIMessages(history)
      }
    } catch {
      if (conversationId.value === id) {
        chat.messages.value = []
      }
    } finally {
      if (conversationId.value === id) {
        hydrating.value = false
      }
    }

    const queued = conversations.takeQueuedMessage()
    if (queued) {
      await chat.sendMessage({ text: queued })
    }

    await focusComposer()
  },
  { immediate: true },
)

async function scrollToNewest(): Promise<void> {
  await nextTick()
  const area = scrollArea.value
  if (area) {
    area.scrollTop = area.scrollHeight
  }
}

async function focusComposer(): Promise<void> {
  await nextTick()
  await composer.value?.focus()
}

function toggleAccount(event: Event): void {
  accountMenu.value?.toggle(event)
}

async function newConversation(): Promise<void> {
  const created = await conversations.create()
  await router.push({ name: 'conversations', params: { id: created.id } })
}

async function selectSuggestion(prompt: string): Promise<void> {
  draft.value = prompt
  await focusComposer()
}

async function submit(): Promise<void> {
  const text = draft.value.trim()
  if (!text || busy.value) {
    return
  }

  // No conversation yet: create one, hand the text over, and let the route
  // watcher send it once the new id is in place.
  if (!conversationId.value) {
    const created = await conversations.create()
    draft.value = ''
    conversations.queueMessage(text)
    await router.push({ name: 'conversations', params: { id: created.id } })
    return
  }

  draft.value = ''
  await chat.sendMessage({ text })
}

function stop(): void {
  void chat.stop()
}

async function signOut(): Promise<void> {
  await session.signOut()
  await router.replace({ name: 'sign-in' })
}
</script>

<template>
  <RootLayout v-model:collapsed="collapsed" @new-conversation="newConversation">
    <template #title>{{ title }}</template>

    <template #sidebar>
      <SidebarGroup title="Projects" storage-key="projects" />
      <SidebarGroup title="Recents" storage-key="recents">
        <ConversationList
          v-model:active-id="activeId"
          :conversations="conversations.conversations"
          :loading="conversations.loading"
          :error="conversations.error"
        />
      </SidebarGroup>
    </template>

    <template #account="{ collapsed }">
      <!-- Tertiary: no fill at rest, Line at 40% on hover, no border. A plain
           button rather than a PrimeVue one, whose own font-size and hover
           would otherwise set it apart from every other tertiary. -->
      <button
        type="button"
        class="flex w-full cursor-pointer items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-body-sm text-ink transition-colors hover:bg-line/40 active:bg-line/60 motion-reduce:transition-none"
        :class="collapsed ? 'justify-center' : ''"
        aria-label="Account"
        aria-haspopup="true"
        aria-controls="account_menu"
        @click="toggleAccount"
      >
        <Avatar :label="initial" shape="circle" class="size-6 shrink-0 text-caption" />
        <span v-if="!collapsed" class="min-w-0 flex-1 truncate max-sm:hidden">
          {{ session.user?.email }}
        </span>
      </button>
      <Menu id="account_menu" ref="accountMenu" :model="accountItems" :popup="true" />
    </template>

    <template v-if="conversationId">
      <div ref="scrollArea" class="min-h-0 flex-1 overflow-y-auto px-6 py-8">
        <MessageList :messages="messages" :working="working" />
        <p
          v-if="errorMessage"
          role="alert"
          class="mx-auto mt-4 max-w-3xl text-body-sm text-subtext"
        >
          {{ errorMessage }}
        </p>
      </div>
      <div class="px-6 pb-6">
        <div class="mx-auto w-full max-w-3xl">
          <MessageComposer
            ref="composer"
            v-model="draft"
            :disabled="!canSend"
            :busy="busy"
            @submit="submit"
            @stop="stop"
          />
        </div>
      </div>
    </template>

    <template v-else>
      <div class="min-h-0 flex-1 overflow-y-auto">
        <!-- Centered horizontally, but anchored near the top rather than
             vertically centered: the composer sits in the upper-middle of the
             page, as on v0 and MiniMax. -->
        <div class="flex min-h-full flex-col items-center px-6 pt-[17vh] pb-16">
          <h1 class="text-center text-heading-lg font-medium">What can I help you with?</h1>
          <div class="mt-8 w-full max-w-3xl">
            <MessageComposer
              ref="composer"
              v-model="draft"
              :disabled="!canSend"
              :busy="busy"
              @submit="submit"
              @stop="stop"
            />
            <div class="mt-4">
              <SuggestionChips @select="selectSuggestion" />
            </div>
          </div>
        </div>
      </div>
    </template>
  </RootLayout>

  <SettingsDialog v-model="settingsOpen" />
</template>
