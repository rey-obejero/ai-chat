import { DefaultChatTransport, isTextUIPart, type UIMessage } from 'ai'

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

/**
 * The server owns history (ADR-0022), so only the newest text is sent, to the
 * URL of the conversation currently open.
 */
export function createConversationTransport(
  conversationId: () => string | null,
): DefaultChatTransport<UIMessage> {
  return new DefaultChatTransport<UIMessage>({
    api: '/api/v1/conversations',
    prepareSendMessagesRequest: ({ messages }) => ({
      api: `/api/v1/conversations/${conversationId()}/messages`,
      body: { content: lastUserText(messages) },
    }),
  })
}
