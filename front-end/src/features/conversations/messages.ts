import { DefaultChatTransport, isTextUIPart, type UIMessage } from 'ai'

import { ApiError, readProblem } from '@/lib/api'
import type { Message } from './api'

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
 * The server owns history (ADR-0022), so only the newest text is sent, to the
 * URL of the conversation currently open.
 */
export function createConversationTransport(
  conversationId: () => string | null,
): DefaultChatTransport<UIMessage> {
  return new DefaultChatTransport<UIMessage>({
    api: '/api/v1/conversations',
    fetch: problemAwareFetch,
    prepareSendMessagesRequest: ({ messages }) => ({
      api: `/api/v1/conversations/${conversationId()}/messages`,
      body: { content: lastUserText(messages) },
    }),
  })
}
