import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import type { DefaultChatTransport, UIMessage } from 'ai'
import PrimeVue from 'primevue/config'
import Tooltip from 'primevue/tooltip'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import MessageActions from '@/features/conversations/components/MessageActions.vue'
import {
  beginAppend,
  buildQuote,
  conversationAction,
  createConversationTransport,
  messageClientId,
  resetConversationAction,
  setConversationAction,
  toUIMessages,
  type ConversationAction,
} from '@/features/conversations/messages'

function userMessage(id = 'm1', text = 'hi'): UIMessage {
  return { id, role: 'user', parts: [{ type: 'text', text }] }
}

function assistantMessage(id = 'm2', text = 'hello'): UIMessage {
  return { id, role: 'assistant', parts: [{ type: 'text', text }] }
}

function mountActions(message: UIMessage, role: 'user' | 'assistant'): VueWrapper {
  return mount(MessageActions, {
    props: { message, role },
    global: {
      directives: { tooltip: Tooltip },
      plugins: [PrimeVue],
    },
  })
}

/** The one logical write `AbstractChat` hands the transport. */
function send(transport: DefaultChatTransport<UIMessage>, messages: UIMessage[]) {
  return transport.sendMessages({
    chatId: 'conv-1',
    messages,
    trigger: 'submit-message',
    messageId: undefined,
    headers: {},
    body: undefined,
    metadata: undefined,
    abortSignal: undefined,
  })
}

describe('MessageActions action set', () => {
  it('offers Copy, Quote and Edit on a user message', () => {
    const wrapper = mountActions(userMessage(), 'user')

    expect(wrapper.findAll('button').map((button) => button.attributes('aria-label'))).toEqual([
      'Copy message',
      'Quote message',
      'Edit message',
    ])
  })

  it('offers Copy, Quote and Regenerate on an assistant message', () => {
    const wrapper = mountActions(assistantMessage(), 'assistant')

    expect(wrapper.findAll('button').map((button) => button.attributes('aria-label'))).toEqual([
      'Copy message',
      'Quote message',
      'Regenerate response',
    ])
  })
})

describe('MessageActions copy', () => {
  it('copies the joined text and confirms for 1.5 seconds', async () => {
    vi.useFakeTimers()
    const writeText = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', { clipboard: { writeText } })

    const wrapper = mountActions(
      {
        id: 'm2',
        role: 'assistant',
        parts: [
          { type: 'text', text: 'Hello ' },
          { type: 'text', text: 'world' },
        ],
      },
      'assistant',
    )

    await wrapper.find('button[aria-label="Copy message"]').trigger('click')
    await flushPromises()

    expect(writeText).toHaveBeenCalledTimes(1)
    expect(writeText).toHaveBeenCalledWith('Hello world')
    expect(wrapper.text()).toContain('Copied')
    expect(wrapper.find('button[aria-label="Copied"]').exists()).toBe(true)

    vi.advanceTimersByTime(1600)
    await flushPromises()

    expect(wrapper.find('button[aria-label="Copy message"]').exists()).toBe(true)
    expect(wrapper.text()).not.toContain('Copied')

    vi.useRealTimers()
  })
})

describe('MessageActions emits', () => {
  it('emits quote', async () => {
    const wrapper = mountActions(userMessage(), 'user')

    await wrapper.find('button[aria-label="Quote message"]').trigger('click')

    expect(wrapper.emitted('quote')).toBeDefined()
  })

  it('emits edit on a user message', async () => {
    const wrapper = mountActions(userMessage(), 'user')

    await wrapper.find('button[aria-label="Edit message"]').trigger('click')

    expect(wrapper.emitted('edit')).toBeDefined()
  })

  it('emits regenerate on an assistant message', async () => {
    const wrapper = mountActions(assistantMessage(), 'assistant')

    await wrapper.find('button[aria-label="Regenerate response"]').trigger('click')

    expect(wrapper.emitted('regenerate')).toBeDefined()
  })
})

describe('buildQuote', () => {
  it('attributes an assistant message to Assistant', () => {
    expect(buildQuote('assistant', 'hello')).toBe('> Assistant: hello\n\n')
  })

  it('attributes a user message to You', () => {
    expect(buildQuote('user', 'hi')).toBe('> You: hi\n\n')
  })

  it('keeps only the first 20 lines of a long message', () => {
    const lines = Array.from({ length: 25 }, (_, index) => `line ${index}`)

    const quote = buildQuote('assistant', lines.join('\n'))

    expect(quote).toBe(`> Assistant: ${lines.slice(0, 20).join('\n')}\n\n`)
    expect(quote).not.toContain('line 20')
  })
})

describe('createConversationTransport routing', () => {
  beforeEach(() => {
    resetConversationAction()
  })

  it('posts the newest user text to the append route with the client id', async () => {
    const action: ConversationAction = { kind: 'append', clientId: 'client-append-1' }
    const fetchMock = vi.fn().mockResolvedValue(new Response('', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    const transport = createConversationTransport(
      () => 'conv-1',
      () => action,
    )

    await send(transport, [userMessage('m1', 'hello there')])

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/v1/conversations/conv-1/messages')

    const body = JSON.parse(init.body as string) as { content: string; client_id: string }
    expect(body).toEqual({ content: 'hello there', client_id: action.clientId })
    expect(typeof body.client_id).toBe('string')
    expect(body.client_id.length).toBeGreaterThan(0)
    expect(body.client_id).toBe(action.clientId)
  })

  it('posts the newest user text to the edit route of the target message', async () => {
    const action: ConversationAction = { kind: 'edit', messageId: 'm1', clientId: 'client-edit-1' }
    const fetchMock = vi.fn().mockResolvedValue(new Response('', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    const transport = createConversationTransport(
      () => 'conv-1',
      () => action,
    )

    await send(transport, [userMessage('m1', 'hello there')])

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/v1/conversations/conv-1/messages/m1/edit')

    const body = JSON.parse(init.body as string) as { content: string; client_id: string }
    expect(body).toEqual({ content: 'hello there', client_id: action.clientId })
    expect(body.client_id).toBe(action.clientId)
  })

  it('posts only the client id to the regenerate route of the target message', async () => {
    const action: ConversationAction = {
      kind: 'regenerate',
      messageId: 'm2',
      clientId: 'client-regenerate-1',
    }
    const fetchMock = vi.fn().mockResolvedValue(new Response('', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    const transport = createConversationTransport(
      () => 'conv-1',
      () => action,
    )

    await send(transport, [userMessage('m1', 'hello there')])

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/v1/conversations/conv-1/messages/m2/regenerate')

    const body = JSON.parse(init.body as string) as { client_id: string }
    expect(body).toEqual({ client_id: action.clientId })
    expect(typeof body.client_id).toBe('string')
    expect(body.client_id.length).toBeGreaterThan(0)
    expect(body.client_id).toBe(action.clientId)
  })

  it('mints a fresh key for every append, so a second send is not a replay of the first', async () => {
    const first = beginAppend()
    const second = beginAppend()
    expect(second).not.toBe(first)

    const fetchMock = vi.fn().mockResolvedValue(new Response('', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    await send(
      createConversationTransport(
        () => 'conv-1',
        () => conversationAction.value,
      ),
      [userMessage('m2', 'a second message')],
    )

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(JSON.parse(init.body as string)).toEqual({
      content: 'a second message',
      client_id: second,
    })
  })

  it('addresses an edit by the key the turn was created with', async () => {
    const [turn] = toUIMessages([
      {
        id: 'server-id',
        role: 'user',
        content: 'hello there',
        created_at: '2026-01-01T00:00:00Z',
        client_id: 'turn-key-1',
      },
    ])
    const fetchMock = vi.fn().mockResolvedValue(new Response('', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    // What the view does for a turn this session sent: the local id stays in the
    // path, and the key its send carried is what identifies the row.
    setConversationAction({ kind: 'edit', messageId: 'local-id', clientId: messageClientId(turn) })

    await send(
      createConversationTransport(
        () => 'conv-1',
        () => conversationAction.value,
      ),
      [turn],
    )

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/v1/conversations/conv-1/messages/local-id/edit')
    expect(JSON.parse(init.body as string)).toEqual({
      content: 'hello there',
      client_id: 'turn-key-1',
    })
  })
})
