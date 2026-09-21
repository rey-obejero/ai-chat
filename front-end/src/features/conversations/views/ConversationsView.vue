<script setup lang="ts">
import Avatar from 'primevue/avatar'
import Button from 'primevue/button'
import Menu from 'primevue/menu'
import type { MenuItem } from 'primevue/menuitem'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import IconLibrary from '~icons/lucide/library'
import IconPanelLeftClose from '~icons/lucide/panel-left-close'
import IconPanelLeftOpen from '~icons/lucide/panel-left-open'
import IconSparkles from '~icons/lucide/sparkles'
import IconSquarePen from '~icons/lucide/square-pen'

import { useSessionStore } from '@/features/auth'
import ConversationList from '../components/ConversationList.vue'
import MessageComposer from '../components/MessageComposer.vue'
import { useConversationsStore } from '../stores/conversations'

const session = useSessionStore()
const conversations = useConversationsStore()
const router = useRouter()

const collapsed = ref(localStorage.getItem('sidebar-collapsed') === 'true')
const draft = ref('')
const accountMenu = ref()
const activeId = ref<string | null>(null)

const canSend = computed(() => draft.value.trim().length > 0)
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

onMounted(() => {
  void conversations.load()
})

function toggleCollapsed(): void {
  collapsed.value = !collapsed.value
}

function toggleAccount(event: Event): void {
  accountMenu.value?.toggle(event)
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
      <div class="flex flex-1 items-center justify-center px-6">
        <div class="w-full">
          <h1 class="mx-auto max-w-4xl text-center text-heading-lg font-semibold sm:text-display">
            Ask anything about your documents.
          </h1>
          <div class="mt-8">
            <MessageComposer v-model="draft" :disabled="!canSend" />
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
