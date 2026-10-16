import { setTimeout as delay } from 'node:timers/promises'

import { flushPromises, mount, type DOMWrapper, type VueWrapper } from '@vue/test-utils'
import ConfirmationService from 'primevue/confirmationservice'
import PrimeVue from 'primevue/config'
import type { MenuItem } from 'primevue/menuitem'
import Tooltip from 'primevue/tooltip'
import { createPinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, type PropType } from 'vue'
import { createMemoryHistory, createRouter, type Router } from 'vue-router'

import {
  deleteConversation,
  listConversations,
  listMessages,
  type Conversation,
  type ConversationPage,
} from '@/features/conversations/api'
import ConversationsView from '@/features/conversations/views/ConversationsView.vue'

vi.mock('@/features/conversations/api', () => ({
  createConversation: vi.fn(),
  deleteConversation: vi.fn(),
  listConversations: vi.fn(),
  listMessages: vi.fn(),
  updateConversation: vi.fn(),
}))

vi.mock('@/features/auth', () => ({
  useSessionStore: () => ({ user: { email: 'ada@example.com' }, signOut: vi.fn() }),
}))

/** The popup teleports its items to the body; rendering them in place is clickable. */
const MenuStub = defineComponent({
  name: 'MenuStub',
  props: {
    model: { type: Array as PropType<MenuItem[]>, default: () => [] },
  },
  expose: ['toggle'],
  methods: {
    toggle(): void {},
  },
  template: `<div class="menu-stub">
    <template v-for="(item, index) in model" :key="index">
      <hr v-if="item.separator" />
      <button v-else type="button" @click="item.command?.()">{{ item.label }}</button>
    </template>
  </div>`,
})

// The view focuses and seeds the composer; a bare stub would throw on both.
const MessageComposerStub = defineComponent({
  name: 'MessageComposer',
  props: { modelValue: String, disabled: Boolean, busy: Boolean },
  emits: ['update:modelValue', 'submit', 'stop'],
  methods: {
    focus(): void {},
    insert(): void {},
  },
  template: '<div class="composer-stub" />',
})

const listMock = vi.mocked(listConversations)
const listMessagesMock = vi.mocked(listMessages)
const deleteMock = vi.mocked(deleteConversation)

const mounted: VueWrapper[] = []

function conversation(overrides: Partial<Conversation> & { id: string }): Conversation {
  return {
    title: `Conversation ${overrides.id}`,
    created_at: '2026-01-01T00:00:00Z',
    is_pinned: false,
    is_favourite: false,
    is_archived: false,
    last_activity_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

function page(items: Conversation[], nextCursor: string | null = null): ConversationPage {
  return { items, next_cursor: nextCursor }
}

async function mountView(
  path = '/application/conversations',
): Promise<{ wrapper: VueWrapper; router: Router }> {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: '/application/conversations/:id?',
        name: 'conversations',
        component: { template: '<div />' },
      },
    ],
  })
  await router.push(path)
  await router.isReady()

  const wrapper = mount(ConversationsView, {
    global: {
      plugins: [createPinia(), router, PrimeVue, ConfirmationService],
      directives: { tooltip: Tooltip },
      stubs: {
        Menu: MenuStub,
        MessageComposer: MessageComposerStub,
        MessageList: true,
        SuggestionChips: true,
        SettingsDialog: true,
      },
    },
  })
  mounted.push(wrapper)
  await flushPromises()
  return { wrapper, router }
}

/** The debounce is 250ms, so a term's request lands just after that. */
async function settleDebounce(): Promise<void> {
  await delay(300)
  await flushPromises()
}

function searchField(wrapper: VueWrapper): DOMWrapper<Element> {
  return wrapper.find('input[aria-label="Search conversations"]')
}

async function askToDelete(wrapper: VueWrapper): Promise<void> {
  await wrapper.find('button[aria-label="Conversation actions"]').trigger('click')
  const items = wrapper.findAll('.menu-stub button')
  await items.find((button) => button.text() === 'Delete')!.trigger('click')
  await flushPromises()
}

function clickDialogButton(button: 'accept' | 'reject'): void {
  document.body.querySelector<HTMLButtonElement>(`.p-confirmdialog-${button}-button`)!.click()
}

beforeEach(() => {
  vi.resetAllMocks()
  listMock.mockResolvedValue(page([conversation({ id: 'c1', title: 'First' })]))
  listMessagesMock.mockResolvedValue([])
  deleteMock.mockResolvedValue(undefined)
})

afterEach(() => {
  // The confirmation teleports to the body; dropping it per test keeps one
  // dialog from answering the next test's query.
  mounted.forEach((wrapper) => wrapper.unmount())
  mounted.length = 0
})

describe('ConversationsView sidebar search', () => {
  it('queries the server once for a burst of keystrokes', async () => {
    const { wrapper } = await mountView()
    expect(listMock).toHaveBeenCalledTimes(1)

    const field = searchField(wrapper)
    await field.setValue('mi')
    await field.setValue('milk')

    // Still debouncing: no second request yet.
    expect(listMock).toHaveBeenCalledTimes(1)

    await settleDebounce()

    expect(listMock).toHaveBeenCalledTimes(2)
    expect(listMock).toHaveBeenLastCalledWith({ q: 'milk', includeArchived: true })
  })

  it('states No matches for a term the server cannot match', async () => {
    const { wrapper } = await mountView()
    listMock.mockResolvedValue(page([]))

    await searchField(wrapper).setValue('zzz')
    await settleDebounce()

    expect(wrapper.text()).toContain('No matches')
  })

  it('clears the term on Escape', async () => {
    const { wrapper } = await mountView()
    const field = searchField(wrapper)

    await field.setValue('milk')
    await settleDebounce()
    expect(listMock).toHaveBeenLastCalledWith({ q: 'milk', includeArchived: true })

    await field.trigger('keydown.escape')
    await flushPromises()

    expect((field.element as HTMLInputElement).value).toBe('')
    expect(listMock).toHaveBeenLastCalledWith({ q: '', includeArchived: true })
  })
})

describe('ConversationsView sidebar sections', () => {
  it('splits the list into Pinned, Recents and Archived', async () => {
    listMock.mockResolvedValue(
      page([
        conversation({ id: 'p', title: 'Pinned chat', is_pinned: true }),
        conversation({ id: 'r', title: 'Recent chat' }),
        conversation({ id: 'a', title: 'Archived chat', is_archived: true }),
      ]),
    )

    const { wrapper } = await mountView()

    const groups = wrapper.findAll('section.sidebar-group')
    expect(groups.map((group) => group.find('button').text())).toEqual([
      'Projects',
      'Pinned',
      'Recents',
      'Archived',
    ])
    expect(wrapper.findAll('section.sidebar-group')[3]!.text()).toContain('Archived chat')
  })

  it('leaves Pinned and Archived out while they are empty', async () => {
    const { wrapper } = await mountView()

    const groups = wrapper.findAll('section.sidebar-group')
    expect(groups.map((group) => group.find('button').text())).toEqual(['Projects', 'Recents'])
  })

  it('offers the next page once the first one is short', async () => {
    listMock.mockResolvedValueOnce(page([conversation({ id: 'c1', title: 'First' })], 'cursor-1'))
    const { wrapper } = await mountView()

    const more = wrapper.findAll('button').find((button) => button.text() === 'Load more')
    expect(more).toBeDefined()

    listMock.mockResolvedValueOnce(page([conversation({ id: 'c2', title: 'Second' })]))
    await more!.trigger('click')
    await flushPromises()

    expect(listMock).toHaveBeenLastCalledWith({
      q: '',
      includeArchived: true,
      cursor: 'cursor-1',
    })
  })
})

describe('ConversationsView delete', () => {
  it('asks first and names the conversation', async () => {
    const { wrapper } = await mountView()

    await askToDelete(wrapper)

    expect(document.body.querySelector('.p-confirmdialog-message')?.textContent).toContain('First')
    expect(deleteMock).not.toHaveBeenCalled()
  })

  it('deletes on confirmation and drops the row', async () => {
    const { wrapper } = await mountView()

    await askToDelete(wrapper)
    clickDialogButton('accept')
    await flushPromises()

    expect(deleteMock).toHaveBeenCalledWith('c1')
    expect(wrapper.text()).not.toContain('First')
  })

  it('leaves the conversation alone when the confirmation is cancelled', async () => {
    const { wrapper } = await mountView()

    await askToDelete(wrapper)
    clickDialogButton('reject')
    await flushPromises()

    expect(deleteMock).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('First')
  })

  it('returns to the conversations index when the open conversation is deleted', async () => {
    const { wrapper, router } = await mountView('/application/conversations/c1')

    await askToDelete(wrapper)
    clickDialogButton('accept')
    await flushPromises()

    expect(deleteMock).toHaveBeenCalledWith('c1')
    expect(router.currentRoute.value.name).toBe('conversations')
    expect(router.currentRoute.value.params.id).toBeUndefined()
  })
})
