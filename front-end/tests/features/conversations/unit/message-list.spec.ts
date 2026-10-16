import { mount, type VueWrapper } from '@vue/test-utils'
import type { UIMessage } from 'ai'
import PrimeVue from 'primevue/config'
import Tooltip from 'primevue/tooltip'
import { describe, expect, it } from 'vitest'

import MessageContent from '@/features/conversations/components/MessageContent.vue'
import MessageList from '@/features/conversations/components/MessageList.vue'

function message(role: 'user' | 'assistant' | 'system', text: string): UIMessage {
  return { id: role, role, parts: [{ type: 'text', text }] }
}

function mountList(messages: UIMessage[]): VueWrapper {
  return mount(MessageList, {
    props: { messages, working: false },
    global: { plugins: [PrimeVue], directives: { tooltip: Tooltip } },
  })
}

describe('MessageList system caption', () => {
  it('renders a system message as a centred Subtext caption', () => {
    const wrapper = mountList([message('system', 'Model set to Model B')])

    const caption = wrapper.find('p.text-center')
    expect(caption.text()).toBe('Model set to Model B')
    expect(caption.classes()).toContain('text-subtext')
    expect(caption.classes()).toContain('text-body-sm')
  })

  it('does not render it as an ordinary turn', () => {
    const wrapper = mountList([
      message('user', 'hello'),
      message('system', 'Model set to Model B'),
      message('assistant', 'hi'),
    ])

    // One turn per real message; the caption is not one of them, so it carries
    // neither a role label nor a row of actions.
    expect(wrapper.findAll('.turn')).toHaveLength(2)
    expect(wrapper.findAll('.message-actions')).toHaveLength(2)
    expect(wrapper.findAll('.turn').some((turn) => turn.text().includes('Model set'))).toBe(false)
  })

  it('keeps a caption literal rather than rendering it as Markdown', () => {
    const wrapper = mountList([message('system', '**Model set** to `B`')])

    expect(wrapper.find('strong').exists()).toBe(false)
    expect(wrapper.find('code').exists()).toBe(false)
    expect(wrapper.text()).toContain('**Model set** to `B`')
  })
})

describe('MessageContent system role', () => {
  it('renders the caption centred in Subtext at body-sm', () => {
    const wrapper = mount(MessageContent, {
      props: { role: 'system', text: 'Model set to Model B' },
    })

    const caption = wrapper.find('p')
    expect(caption.classes()).toEqual(
      expect.arrayContaining(['text-center', 'text-subtext', 'text-body-sm']),
    )
    expect(wrapper.find('.markdown').exists()).toBe(false)
  })
})
