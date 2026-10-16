import { ref, type Ref } from 'vue'
import { DefaultChatTransport, isTextUIPart, type UIMessage } from 'ai'

import { ApiError, readProblem } from '@/lib/api'
import type { Message } from './api'

/** Which write the next request is: a new message, an edit, or a regeneration. */
export type ConversationActionKind = 'append' | 'edit' | 'regenerate'

export interface ConversationAction {
  kind: ConversationActionKind
  /**
   * The message being edited or regenerated, as the router addresses it: the
   * local id for a turn of this session, the server uuid for a restored one.
   * Absent for an append.
   */
  messageId?: string
  /**
   * The write's key. An append mints the key that names its new user turn; an
   * edit carries the key of the turn it targets, which is how a turn this
   * session never learned the server uuid of is addressed; a regenerate mints a
   * fresh key for its reply. Absent only for a restored turn that has no key,
   * which then resolves by the uuid in its path.
   */
  clientId?: string
}

/**
 * A v4 uuid. `crypto.randomUUID` is secure-context only and the app also runs
 * on a non-secure origin, so format random bytes by hand when it is missing.
 */
function newClientId(): string {
  if (typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = [...bytes].map((byte) => byte.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

/**
 * The action the view sets immediately before a call and resets straight after,
 * so the transport reads it for the request it is about to make.
 */
export const conversationAction: Ref<ConversationAction> = ref({ kind: 'append' })

/**
 * Start an append and return the key naming the user turn it creates.
 *
 * The key is minted here, before `sendMessage`, and not in the transport: the
 * optimistic turn has to carry the same key as `metadata`, so an edit later in
 * the session can name that turn by it (its local id is not a server uuid). The
 * transport therefore never invents a key of its own.
 */
export function beginAppend(): string {
  const clientId = newClientId()
  conversationAction.value = { kind: 'append', clientId }
  return clientId
}

/**
 * Point the next request at an edit or a regeneration. Set immediately before
 * the call; reset straight after with {@link resetConversationAction}.
 *
 * An edit passes the target turn's key, which the route resolves the row by and
 * which also keys the reply the edit streams — so a retry of the same edit is a
 * replay rather than a second reply. A regenerate mints its own key for the new
 * reply, because the target is addressed by its server uuid.
 */
export function setConversationAction(action: {
  kind: 'edit' | 'regenerate'
  messageId: string
  clientId?: string
}): void {
  conversationAction.value = {
    kind: action.kind,
    messageId: action.messageId,
    clientId: action.clientId ?? newClientId(),
  }
}

/** Return the next request to a plain append. */
export function resetConversationAction(): void {
  conversationAction.value = { kind: 'append' }
}

/**
 * The key that created a turn, carried on its `metadata` — set by
 * `toUIMessages` for a restored turn and by a send for an optimistic one.
 */
export function messageClientId(message: UIMessage): string | undefined {
  const { metadata } = message
  if (metadata === null || typeof metadata !== 'object' || !('clientId' in metadata)) {
    return undefined
  }
  return typeof metadata.clientId === 'string' ? metadata.clientId : undefined
}

/**
 * FR-14's quote format: a `> You:` or `> Assistant:` marker on the first line,
 * at most the first 20 lines of the message, closed by a blank line.
 */
export function buildQuote(role: 'user' | 'assistant', text: string): string {
  const label = role === 'user' ? 'You' : 'Assistant'
  const firstLines = text.split('\n').slice(0, 20).join('\n')
  return `> ${label}: ${firstLines}\n\n`
}

export function messageText(message: UIMessage): string {
  return message.parts
    .filter(isTextUIPart)
    .map((part) => part.text)
    .join('')
}

export function lastUserText(messages: UIMessage[]): string {
  const lastUser = [...messages].reverse().find((message) => message.role === 'user')
  return lastUser ? messageText(lastUser) : ''
}

/** Render persisted history through the same shape `useChat` produces. */
export function toUIMessages(history: Message[]): UIMessage[] {
  return history.map((message) => ({
    id: message.id,
    role: message.role,
    parts: [{ type: 'text' as const, text: message.content }],
    // The turn's key rides on its metadata so an edit can address a restored
    // turn the same way it addresses one this session sent.
    ...(message.client_id ? { metadata: { clientId: message.client_id } } : {}),
  }))
}

/** Readable copy for the problem codes the API can return. */
const ERROR_COPY: Record<string, string> = {
  LLM_NOT_CONFIGURED: 'The assistant has not been configured yet.',
  LLM_PROVIDER_ERROR: 'The assistant could not be reached. Try again.',
  RATE_LIMITED: 'Too many messages too quickly. Wait a moment, then try again.',
  QUOTA_EXCEEDED: 'You have used your token quota for this period. Try again after it resets.',
  NOT_AUTHENTICATED: 'Your session has expired. Sign in again.',
  NOT_FOUND: 'That conversation no longer exists.',
  VALIDATION_ERROR: 'That message could not be sent.',
  INTERNAL_ERROR: 'Something went wrong. Try again.',
}

/** Turn a transport failure into copy a person can act on. */
export function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    return ERROR_COPY[error.code] ?? error.message
  }
  return 'Something went wrong. Try again.'
}

/**
 * Reject with the parsed problem+json, so `useChat` carries the code and detail
 * rather than the raw response text.
 */
async function problemAwareFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const response = await fetch(input, init)
  if (response.ok) {
    return response
  }
  throw await readProblem(response)
}

/**
 * The server owns history (ADR-0022), so only the newest text is sent. The
 * action picked by the view selects the route — append, edit, or regenerate —
 * and carries the write's key, which the API uses to identify the turn a write
 * names and to make a retry a no-op rather than a duplicate message.
 *
 * The path segment stays the id the view holds: the local id for a turn this
 * session sent, the server uuid for a restored one. The API resolves it as a
 * uuid first and falls back to the key in the body, so both work.
 */
export function createConversationTransport(
  conversationId: () => string | null,
  action: () => ConversationAction,
): DefaultChatTransport<UIMessage> {
  return new DefaultChatTransport<UIMessage>({
    api: '/api/v1/conversations',
    fetch: problemAwareFetch,
    prepareSendMessagesRequest: ({ messages }) => {
      const id = conversationId()
      const current = action()
      // A restored turn with no key is addressed by the uuid in its path alone.
      const key = current.clientId === undefined ? {} : { client_id: current.clientId }

      switch (current.kind) {
        case 'edit':
          return {
            api: `/api/v1/conversations/${id}/messages/${current.messageId}/edit`,
            body: { content: lastUserText(messages), ...key },
          }
        case 'regenerate':
          return {
            api: `/api/v1/conversations/${id}/messages/${current.messageId}/regenerate`,
            body: key,
          }
        case 'append':
          return {
            api: `/api/v1/conversations/${id}/messages`,
            body: { content: lastUserText(messages), ...key },
          }
      }
    },
  })
}
