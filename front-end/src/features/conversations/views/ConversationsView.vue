<script setup lang="ts">
import { useChat } from '@ai-sdk/vue'
import type { UIMessage } from 'ai'
import Avatar from 'primevue/avatar'
import ConfirmDialog from 'primevue/confirmdialog'
import Menu from 'primevue/menu'
import type { MenuItem } from 'primevue/menuitem'
import { useConfirm } from 'primevue/useconfirm'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import IconSearch from '~icons/lucide/search'

import RootLayout from '@/components/layouts/RootLayout.vue'
import SidebarGroup from '@/components/layouts/SidebarGroup.vue'
import { useSessionStore } from '@/features/auth'
import { SettingsDialog } from '@/features/settings'
import { listMessages, type Conversation } from '../api'
import ConversationList from '../components/ConversationList.vue'
import MessageComposer from '../components/MessageComposer.vue'
import MessageList from '../components/MessageList.vue'
import SuggestionChips from '../components/SuggestionChips.vue'
import {
  beginAppend,
  buildQuote,
  conversationAction,
  createConversationTransport,
  describeError,
  messageClientId,
  messageText,
  resetConversationAction,
  setConversationAction,
  toUIMessages,
} from '../messages'
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
const searchTerm = ref('')
const confirm = useConfirm()
let searchTimer: ReturnType<typeof setTimeout> | undefined

const conversationId = computed(() => {
  const id = route.params.id
  return typeof id === 'string' && id.length > 0 ? id : null
})

const title = computed(
  () => conversations.conversations.find((item) => item.id === conversationId.value)?.title ?? '',
)

const chat = useChat({
  transport: createConversationTransport(
    () => conversationId.value,
    () => conversationAction.value,
  ),
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

/**
 * Pinned, then the main list, then Archived (locked decision 7). Recents is the
 * sidebar's standing list and shows while empty; the other two earn a header
 * only once they hold a row.
 */
const sections = computed(() => {
  const groups = [
    { title: 'Pinned', storageKey: 'pinned', conversations: conversations.pinned },
    { title: 'Recents', storageKey: 'recents', conversations: conversations.recents },
    { title: 'Archived', storageKey: 'archived', conversations: conversations.archived },
  ]
  return groups.filter((group) => group.title === 'Recents' || group.conversations.length > 0)
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

// A pending debounce must not outlive the view and write to a disposed store.
onBeforeUnmount(() => clearTimeout(searchTimer))

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
      // The key is minted here so the optimistic turn carries it, exactly as an
      // in-conversation send does.
      await chat.sendMessage({ text: queued, metadata: { clientId: beginAppend() } })
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

/**
 * The list is a server query, so a request per keystroke would be a request per
 * keystroke; the timer collapses a burst into one. The event's own value is read
 * rather than the model's, because `v-model`'s update order is not worth
 * depending on.
 */
function onSearchInput(event: Event): void {
  const term = (event.target as HTMLInputElement).value
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    void conversations.search(term)
  }, 250)
}

/** Escape clears the term and restores the unfiltered list straight away. */
function clearSearch(): void {
  clearTimeout(searchTimer)
  searchTerm.value = ''
  void conversations.search('')
}

function onLoadMore(): void {
  void conversations.loadMore()
}

/** The confirmation names the conversation, so the dialog needs the row, not its id. */
function askDelete(conversation: Conversation): void {
  confirm.require({
    header: 'Delete conversation',
    message: `Delete “${conversation.title}”? Its messages are deleted with it.`,
    acceptLabel: 'Delete',
    rejectLabel: 'Cancel',
    accept: () => void deleteAndReturn(conversation),
  })
}

async function deleteAndReturn(conversation: Conversation): Promise<void> {
  const wasActive = conversation.id === conversationId.value
  if (!(await conversations.remove(conversation.id))) {
    return
  }
  // The transcript is gone, so its route is too: the deleted conversation is
  // the empty state, not a 404.
  if (wasActive) {
    await router.push({ name: 'conversations' })
  }
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
  const clientId = beginAppend()
  await chat.sendMessage({ text, metadata: { clientId } })
}

function stop(): void {
  void chat.stop()
}

async function quoteMessage(message: UIMessage): Promise<void> {
  await composer.value?.insert(
    buildQuote(message.role === 'user' ? 'user' : 'assistant', messageText(message)),
  )
}

async function editMessage(message: UIMessage): Promise<void> {
  if (busy.value) {
    return
  }

  // The turn's own key addresses it in the request, because a user turn sent in
  // this session never learned the server uuid; `messageId` keeps the path and
  // makes the SDK replace that turn in place and drop everything after it.
  const clientId = messageClientId(message)
  setConversationAction({ kind: 'edit', messageId: message.id, clientId })
  try {
    await chat.sendMessage({
      text: messageText(message),
      messageId: message.id,
      metadata: clientId === undefined ? undefined : { clientId },
    })
  } finally {
    resetConversationAction()
  }
}

async function regenerateMessage(message: UIMessage): Promise<void> {
  if (busy.value) {
    return
  }

  // `regenerate` already truncates the chat's own list back to before the
  // assistant message, so truncating it here as well would make it throw.
  setConversationAction({ kind: 'regenerate', messageId: message.id })
  try {
    await chat.regenerate({ messageId: message.id })
  } finally {
    resetConversationAction()
  }
}

async function signOut(): Promise<void> {
  await session.signOut()
  await router.replace({ name: 'sign-in' })
}
</script>

<template>
  <RootLayout v-model:collapsed="collapsed" @new-conversation="newConversation">
    <template #title>{{ title }}</template>

    <template #search="{ collapsed }">
      <!-- The nav's Search row (DESIGN.md — Nav Item): a Nav Item at rest, the
           Text Input it holds once focused. The collapsed rail drops it with
           the groups: a 64px row cannot hold a field. -->
      <div
        v-if="!collapsed"
        class="search-row flex items-center gap-2.5 rounded-lg border border-transparent px-2.5 py-2 transition-colors motion-reduce:transition-none hover:bg-line/40"
      >
        <IconSearch class="size-4 shrink-0 text-icon" stroke-width="2" />
        <input
          v-model="searchTerm"
          type="text"
          class="min-w-0 flex-1 bg-transparent text-body-sm text-ink placeholder:text-subtext"
          placeholder="Search"
          aria-label="Search conversations"
          @input="onSearchInput"
          @keydown.escape="clearSearch"
        />
      </div>
    </template>

    <template #sidebar>
      <SidebarGroup title="Projects" storage-key="projects" />

      <p v-if="conversations.error" role="alert" class="px-2.5 py-2 text-caption text-subtext">
        {{ conversations.error }}
      </p>
      <p
        v-else-if="conversations.pending"
        role="status"
        class="px-2.5 py-2 text-caption text-subtext"
      >
        Loading…
      </p>
      <p
        v-else-if="conversations.noMatches"
        role="status"
        class="px-2.5 py-2 text-caption text-subtext"
      >
        No matches
      </p>

      <template v-else>
        <SidebarGroup
          v-for="section in sections"
          :key="section.storageKey"
          :title="section.title"
          :storage-key="section.storageKey"
        >
          <ConversationList
            v-model:active-id="activeId"
            :conversations="section.conversations"
            @rename="conversations.rename"
            @toggle-pin="conversations.togglePin"
            @toggle-favourite="conversations.toggleFavourite"
            @toggle-archive="conversations.toggleArchive"
            @remove="askDelete"
          />
        </SidebarGroup>

        <button
          v-if="conversations.hasMore"
          type="button"
          class="mt-1 w-full cursor-pointer rounded-lg px-2.5 py-2 text-left text-body-sm text-subtext transition-colors hover:text-ink motion-reduce:transition-none"
          @click="onLoadMore"
        >
          Load more
        </button>
      </template>
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
        <MessageList
          :messages="messages"
          :working="working"
          @quote="quoteMessage"
          @edit="editMessage"
          @regenerate="regenerateMessage"
        />
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
  <ConfirmDialog />
</template>

<style scoped>
/* At rest the row is a Nav Item; focused it becomes the Text Input it holds —
   Paper White with a Line edge (DESIGN.md — Text Input). The 1px edge is in the
   box already (transparent), so nothing shifts as it takes its colour. */
.search-row:focus-within {
  background-color: var(--color-paper-white);
  border-color: var(--color-line);
}

/* The ring follows the row, not the field inside it: the row is the control.
   `:has` keeps it to keyboard focus, as Interaction States requires. */
.search-row:has(input:focus-visible) {
  outline: 2px solid var(--color-ink);
  outline-offset: 2px;
}

.search-row input:focus {
  outline: none;
}
</style>
