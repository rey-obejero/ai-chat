import { setTimeout as delay } from 'node:timers/promises'

import type { UIMessage } from 'ai'
import { flushPromises, mount, type DOMWrapper, type VueWrapper } from '@vue/test-utils'
import ConfirmationService from 'primevue/confirmationservice'
import PrimeVue from 'primevue/config'
import type { MenuItem } from 'primevue/menuitem'
import Tooltip from 'primevue/tooltip'
import { createPinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from 'vitest'
import { defineComponent, ref, type PropType, type Ref } from 'vue'
import { createMemoryHistory, createRouter, type Router } from 'vue-router'

import { ApiError } from '@/lib/api'
import {
  createConversation,
  deleteConversation,
  listConversations,
  listMessages,
  listModels,
  updateConversation,
  type Conversation,
  type ConversationPage,
  type ModelInfo,
} from '@/features/conversations/api'
import NamePromptDialog from '@/features/conversations/components/NamePromptDialog.vue'
import { messageText } from '@/features/conversations/messages'
import ConversationsView from '@/features/conversations/views/ConversationsView.vue'

vi.mock('@/features/conversations/api', () => ({
  createConversation: vi.fn(),
  deleteConversation: vi.fn(),
  listConversations: vi.fn(),
  listMessages: vi.fn(),
  listModels: vi.fn(),
  updateConversation: vi.fn(),
}))

/**
 * The session the view reads the account from, mutable so a test can hand the
 * view an account that has not answered the name prompt or carries no name.
 * The store is mocked rather than the feature's `index.ts`, so the rest of what
 * the feature exports — the verification nudge among it — stays real.
 */
const auth = vi.hoisted(() => ({
  user: { display_name: 'Ada Lovelace', email: 'ada@example.com', name_prompt_seen: true },
  signOut: vi.fn(),
}))
vi.mock('@/features/auth/stores/session', () => ({ useSessionStore: () => auth }))

/** The chat the view drives, as `useChat` hands it over. */
interface ChatStub {
  messages: Ref<UIMessage[]>
  error: Ref<unknown>
  status: Ref<string>
  sendMessage: Mock
  stop: Mock
  regenerate: Mock
}

/**
 * `useChat` is replaced so a test can hand the view a refused turn's problem —
 * the one thing that shows the allowance block's own copy — without a transport.
 * The values are refs, because the view derives its rendered copy from them.
 */
const chat: ChatStub = {
  messages: ref<UIMessage[]>([]),
  error: ref<unknown>(undefined),
  status: ref('ready'),
  sendMessage: vi.fn(),
  stop: vi.fn(),
  regenerate: vi.fn(),
}

vi.mock('@ai-sdk/vue', () => ({ useChat: () => chat }))

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
  props: {
    modelValue: String,
    disabled: Boolean,
    busy: Boolean,
    models: { type: Array as PropType<ModelInfo[]>, default: () => [] },
    model: { type: String as PropType<string | null>, default: null },
  },
  emits: ['update:modelValue', 'update:model', 'submit', 'stop'],
  methods: {
    focus(): void {},
    insert(): void {},
  },
  template: '<div class="composer-stub" />',
})

// The transcript a real MessageList would draw, kept as props so the spec can
// read the turns the view handed it — the model caption among them.
const MessageListStub = defineComponent({
  name: 'MessageList',
  props: {
    messages: { type: Array as PropType<UIMessage[]>, default: () => [] },
    working: Boolean,
  },
  template: '<div class="message-list-stub" />',
})

const SettingsDialogStub = defineComponent({
  name: 'SettingsDialog',
  props: {
    modelValue: Boolean,
    section: { type: String as PropType<string | null>, default: null },
  },
  emits: ['update:modelValue'],
  template: '<div class="settings-dialog-stub" />',
})

const listMock = vi.mocked(listConversations)
const listMessagesMock = vi.mocked(listMessages)
const deleteMock = vi.mocked(deleteConversation)
const createMock = vi.mocked(createConversation)
const updateMock = vi.mocked(updateConversation)
const modelsMock = vi.mocked(listModels)

/** Two served models, so a switch has somewhere to switch to. */
const MODELS: ModelInfo[] = [
  { id: 'model-a', label: 'Model A', is_default: true },
  { id: 'model-b', label: 'Model B', is_default: false },
]

const mounted: VueWrapper[] = []

function conversation(overrides: Partial<Conversation> & { id: string }): Conversation {
  return {
    title: `Conversation ${overrides.id}`,
    created_at: '2026-01-01T00:00:00Z',
    is_pinned: false,
    is_favourite: false,
    is_archived: false,
    model: null,
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
        MessageList: MessageListStub,
        SuggestionChips: true,
        SettingsDialog: SettingsDialogStub,
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

/** Choose a model, as the composer's menu does when one of its items is picked. */
async function chooseModel(wrapper: VueWrapper, model: string): Promise<void> {
  wrapper.findComponent(MessageComposerStub).vm.$emit('update:model', model)
  await flushPromises()
}

async function clickNewConversation(wrapper: VueWrapper): Promise<void> {
  await wrapper
    .findAll('button')
    .find((button) => button.text() === 'New conversation')!
    .trigger('click')
  await flushPromises()
}

async function clickAccountItem(wrapper: VueWrapper, label: string): Promise<void> {
  await wrapper
    .findAll('button')
    .find((button) => button.text() === label)!
    .trigger('click')
  await flushPromises()
}

/** The transcript the view handed the list, which is where a caption lands. */
function transcript(wrapper: VueWrapper): UIMessage[] {
  return wrapper.findComponent(MessageListStub).props('messages') as UIMessage[]
}

beforeEach(() => {
  vi.resetAllMocks()
  chat.messages.value = []
  chat.error.value = undefined
  chat.status.value = 'ready'
  auth.user = { display_name: 'Ada Lovelace', email: 'ada@example.com', name_prompt_seen: true }
  listMock.mockResolvedValue(page([conversation({ id: 'c1', title: 'First' })]))
  listMessagesMock.mockResolvedValue([])
  deleteMock.mockResolvedValue(undefined)
  modelsMock.mockResolvedValue(MODELS)
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

describe('ConversationsView model picker', () => {
  it('hands the served models and the current model to the composer', async () => {
    listMock.mockResolvedValue(page([conversation({ id: 'c1', title: 'First', model: 'model-b' })]))

    const { wrapper } = await mountView('/application/conversations/c1')

    const composer = wrapper.findComponent(MessageComposerStub)
    expect(modelsMock).toHaveBeenCalled()
    expect(composer.props('models')).toEqual(MODELS)
    expect(composer.props('model')).toBe('model-b')
  })

  it('carries a model picked before the first message on the conversation it creates', async () => {
    createMock.mockResolvedValue(conversation({ id: 'c2', model: 'model-b' }))

    const { wrapper } = await mountView()
    await chooseModel(wrapper, 'model-b')
    await clickNewConversation(wrapper)

    expect(createMock).toHaveBeenCalledWith('model-b')
  })

  it('updates the conversation and discloses the switch once it has started', async () => {
    updateMock.mockResolvedValue(conversation({ id: 'c1', model: 'model-b' }))

    const { wrapper } = await mountView('/application/conversations/c1')
    await chooseModel(wrapper, 'model-b')

    expect(updateMock).toHaveBeenCalledWith('c1', { model: 'model-b' })

    const captions = transcript(wrapper)
      .filter((message) => message.role === 'system')
      .map((message) => messageText(message))
    expect(captions).toEqual(['Model set to Model B'])
  })

  it('writes no caption when the server refuses the switch', async () => {
    updateMock.mockRejectedValue(new Error('refused'))

    const { wrapper } = await mountView('/application/conversations/c1')
    await chooseModel(wrapper, 'model-b')

    expect(transcript(wrapper)).toEqual([])
  })

  it('writes nothing for the model the conversation already has', async () => {
    listMock.mockResolvedValue(page([conversation({ id: 'c1', title: 'First', model: 'model-b' })]))

    const { wrapper } = await mountView('/application/conversations/c1')
    await chooseModel(wrapper, 'model-b')

    expect(updateMock).not.toHaveBeenCalled()
    expect(transcript(wrapper)).toEqual([])
  })
})

describe('ConversationsView account menu', () => {
  it('opens the settings dialog at Personalization', async () => {
    const { wrapper } = await mountView()
    expect(wrapper.findComponent(SettingsDialogStub).props('modelValue')).toBe(false)

    await clickAccountItem(wrapper, 'Personalization')

    const dialog = wrapper.findComponent(SettingsDialogStub)
    expect(dialog.props('modelValue')).toBe(true)
    expect(dialog.props('section')).toBe('personalization')
  })

  it('opens the settings dialog at Profile from its own item', async () => {
    const { wrapper } = await mountView()

    await clickAccountItem(wrapper, 'Profile')

    const dialog = wrapper.findComponent(SettingsDialogStub)
    expect(dialog.props('modelValue')).toBe(true)
    expect(dialog.props('section')).toBe('profile')
  })
})

describe('ConversationsView account button', () => {
  it('names the account with the display name and takes its initial', async () => {
    const { wrapper } = await mountView()

    const button = wrapper.find('button[aria-label="Account"]')
    expect(button.text()).toContain('Ada Lovelace')
    expect(button.find('.p-avatar').text()).toBe('A')
  })

  it('falls back to the email when the account has no name', async () => {
    auth.user = { display_name: '', email: 'zoe@example.com', name_prompt_seen: true }

    const { wrapper } = await mountView()

    const button = wrapper.find('button[aria-label="Account"]')
    expect(button.text()).toContain('zoe@example.com')
    expect(button.find('.p-avatar').text()).toBe('Z')
  })
})

describe('ConversationsView name prompt', () => {
  it('leaves an account that has already answered it alone', async () => {
    const { wrapper } = await mountView()

    expect(wrapper.findComponent(NamePromptDialog).exists()).toBe(false)
  })

  it('asks an account that has not answered it yet', async () => {
    auth.user = { display_name: 'Ada Lovelace', email: 'ada@example.com', name_prompt_seen: false }

    const { wrapper } = await mountView()

    expect(wrapper.findComponent(NamePromptDialog).exists()).toBe(true)
  })
})

describe('ConversationsView allowance block', () => {
  it('answers the unverified block with the nudge, not the quota copy', async () => {
    // What an account that has spent the reduced allowance is refused with
    // (ADR-0039): the quota problem, carrying the flag that says verifying the
    // email would lift it.
    chat.error.value = new ApiError({
      type: 'about:blank',
      title: 'Too Many Requests',
      status: 429,
      code: 'QUOTA_EXCEEDED',
      verification_required: true,
    })

    const { wrapper } = await mountView('/application/conversations/c1')

    expect(wrapper.text()).toContain('Verify your email to unlock the full allowance')
    expect(wrapper.text()).toContain('Resend verification email')
    expect(wrapper.text()).not.toContain('You have used your token quota for this period')
  })

  it('keeps the quota copy for a block verification would not lift', async () => {
    chat.error.value = new ApiError({
      type: 'about:blank',
      title: 'Too Many Requests',
      status: 429,
      code: 'QUOTA_EXCEEDED',
    })

    const { wrapper } = await mountView('/application/conversations/c1')

    expect(wrapper.text()).toContain('You have used your token quota for this period')
    expect(wrapper.text()).not.toContain('Resend verification email')
  })
})
