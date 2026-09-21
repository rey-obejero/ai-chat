<script setup lang="ts">
import { useChat } from '@ai-sdk/vue'
import Avatar from 'primevue/avatar'
import Button from 'primevue/button'
import Menu from 'primevue/menu'
import type { MenuItem } from 'primevue/menuitem'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import IconLibrary from '~icons/lucide/library'
import IconPanelLeftClose from '~icons/lucide/panel-left-close'
import IconPanelLeftOpen from '~icons/lucide/panel-left-open'
import IconSparkles from '~icons/lucide/sparkles'
import IconSquarePen from '~icons/lucide/square-pen'

import { useSessionStore } from '@/features/auth'
import { listMessages } from '../api'
import ConversationList from '../components/ConversationList.vue'
import MessageComposer from '../components/MessageComposer.vue'
import MessageList from '../components/MessageList.vue'
import { createConversationTransport, describeError, toUIMessages } from '../messages'
import { useConversationsStore } from '../stores/conversations'

const session = useSessionStore()
const conversations = useConversationsStore()
const route = useRoute()
const router = useRouter()

const collapsed = ref(localStorage.getItem('sidebar-collapsed') === 'true')
const draft = ref('')
const accountMenu = ref()
const scrollArea = ref<HTMLElement | null>(null)
const hydrating = ref(false)

const conversationId = computed(() => {
  const id = route.params.id
  return typeof id === 'string' && id.length > 0 ? id : null
})

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
  { label: 'Settings' },
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

function toggleCollapsed(): void {
  collapsed.value = !collapsed.value
}

function toggleAccount(event: Event): void {
  accountMenu.value?.toggle(event)
}

async function newConversation(): Promise<void> {
  const created = await conversations.create()
  await router.push({ name: 'conversations', params: { id: created.id } })
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
  await router.replace('/sign-in')
}
</script>

<template>
  <div class="flex h-screen bg-paper-white text-ink">
    <aside
      id="sidebar"
      class="flex shrink-0 flex-col border-r border-line bg-canvas transition-[width] duration-200 ease-out motion-reduce:transition-none"
      :class="collapsed ? 'w-16' : 'w-64'"
    >
      <div
        class="flex items-center px-2 pt-3"
        :class="collapsed ? 'justify-center' : 'justify-between'"
      >
        <span v-if="!collapsed" class="px-2.5 text-body font-medium text-ink">AI Chat</span>
        <Button
          text
          rounded
          :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          :aria-expanded="!collapsed"
          aria-controls="sidebar"
          @click="toggleCollapsed"
        >
          <IconPanelLeftClose v-if="!collapsed" class="text-icon" />
          <IconPanelLeftOpen v-else class="text-icon" />
        </Button>
      </div>

      <div class="px-2 pt-2">
        <Button
          text
          fluid
          aria-label="New conversation"
          v-tooltip.right="collapsed ? 'New conversation' : null"
          @click="newConversation"
        >
          <span class="flex w-full items-center gap-2.5" :class="collapsed ? 'justify-center' : ''">
            <IconSquarePen class="shrink-0 text-icon" />
            <span v-if="!collapsed">New conversation</span>
          </span>
        </Button>
      </div>

      <nav class="px-2 pt-1">
        <Button text fluid aria-label="Library" v-tooltip.right="collapsed ? 'Library' : null">
          <span class="flex w-full items-center gap-2.5" :class="collapsed ? 'justify-center' : ''">
            <IconLibrary class="shrink-0 text-icon" />
            <span v-if="!collapsed">Library</span>
          </span>
        </Button>
        <Button text fluid aria-label="Skills" v-tooltip.right="collapsed ? 'Skills' : null">
          <span class="flex w-full items-center gap-2.5" :class="collapsed ? 'justify-center' : ''">
            <IconSparkles class="shrink-0 text-icon" />
            <span v-if="!collapsed">Skills</span>
          </span>
        </Button>
      </nav>

      <div v-if="!collapsed" class="mt-4 min-h-0 flex-1 overflow-y-auto px-2 pb-2">
        <ConversationList
          v-model:active-id="activeId"
          :conversations="conversations.conversations"
          :loading="conversations.loading"
          :error="conversations.error"
        />
      </div>
      <div v-else class="flex-1" />

      <div class="p-2">
        <Button
          text
          fluid
          aria-label="Account"
          aria-haspopup="true"
          aria-controls="account_menu"
          @click="toggleAccount"
        >
          <span class="flex w-full items-center gap-2.5" :class="collapsed ? 'justify-center' : ''">
            <Avatar :label="initial" shape="circle" />
            <span
              v-if="!collapsed"
              class="min-w-0 flex-1 truncate text-left text-body-sm text-subtext"
            >
              {{ session.user?.email }}
            </span>
          </span>
        </Button>
        <Menu id="account_menu" ref="accountMenu" :model="accountItems" :popup="true" />
      </div>
    </aside>

    <main class="flex min-w-0 flex-1 flex-col bg-paper-white">
      <template v-if="conversationId">
        <div ref="scrollArea" class="min-h-0 flex-1 overflow-y-auto px-6 py-8">
          <MessageList :messages="messages" :working="working" />
          <p
            v-if="errorMessage"
            role="alert"
            class="mx-auto mt-4 max-w-2xl text-body-sm text-subtext"
          >
            {{ errorMessage }}
          </p>
        </div>
        <div class="px-6 pb-6">
          <MessageComposer
            v-model="draft"
            :disabled="!canSend"
            :busy="busy"
            @submit="submit"
            @stop="stop"
          />
        </div>
      </template>

      <template v-else>
        <div class="flex flex-1 items-center justify-center px-6">
          <div class="w-full">
            <h1 class="mx-auto max-w-4xl text-center text-heading-lg font-semibold sm:text-display">
              Ask anything about your documents.
            </h1>
            <div class="mt-8">
              <MessageComposer
                v-model="draft"
                :disabled="!canSend"
                :busy="busy"
                @submit="submit"
                @stop="stop"
              />
            </div>
          </div>
        </div>
      </template>
    </main>
  </div>
</template>
