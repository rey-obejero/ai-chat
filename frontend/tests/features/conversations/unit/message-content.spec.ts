import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import MessageContent from '@/features/conversations/components/MessageContent.vue'

function fenceLines(count: number): string {
  return Array.from({ length: count }, (_, index) => `line ${index}`).join('\n')
}

async function mountContent(role: 'user' | 'assistant', text: string): Promise<VueWrapper> {
  const wrapper = mount(MessageContent, { props: { role, text } })
  await flushPromises()
  return wrapper
}

describe('MessageContent', () => {
  it('renders assistant markdown as elements', async () => {
    const wrapper = await mountContent('assistant', '**bold**')

    expect(wrapper.find('strong').exists()).toBe(true)
    expect(wrapper.find('.markdown').exists()).toBe(true)
  })

  it('renders user text literally', async () => {
    const wrapper = await mountContent('user', '**bold**')

    expect(wrapper.find('strong').exists()).toBe(false)
    expect(wrapper.text()).toContain('**bold**')
    expect(wrapper.find('.markdown').exists()).toBe(false)
  })

  it('renders a user fence as a mono block', async () => {
    const wrapper = await mountContent('user', 'before\n```\nconst a = 1\n```')

    expect(wrapper.find('code').exists()).toBe(true)
    expect(wrapper.find('code').text()).toContain('const a = 1')
    expect(wrapper.text()).toContain('before')
  })

  it('copies the raw code and flips the control back', async () => {
    vi.useFakeTimers()
    const writeText = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', { clipboard: { writeText } })

    const wrapper = await mountContent('assistant', '```js\nconst answer = 1\n```')

    await wrapper.find('.md-code__copy').trigger('click')
    await flushPromises()

    expect(writeText).toHaveBeenCalledWith('const answer = 1\n')
    expect(wrapper.find('.md-code__copy').attributes('data-copied')).toBeDefined()

    vi.advanceTimersByTime(1600)
    await flushPromises()
    expect(wrapper.find('.md-code__copy').attributes('data-copied')).toBeUndefined()

    vi.useRealTimers()
  })

  it('expands a long fence and keeps the state across a re-render', async () => {
    const wrapper = await mountContent('assistant', `\`\`\`\n${fenceLines(25)}\n\`\`\``)

    expect(wrapper.find('.md-code').classes()).not.toContain('is-expanded')
    await wrapper.find('.md-code__expand').trigger('click')
    await flushPromises()

    expect(wrapper.find('.md-code').classes()).toContain('is-expanded')
    expect(wrapper.find('.md-code__expand').attributes('aria-expanded')).toBe('true')
    expect(wrapper.find('.md-code__expand').text()).toBe('Show less')

    await wrapper.setProps({ text: `\`\`\`\n${fenceLines(30)}\n\`\`\`` })
    await flushPromises()

    expect(wrapper.find('.md-code').classes()).toContain('is-expanded')
  })

  it('never renders a script element or an event-handler attribute', async () => {
    const wrapper = await mountContent(
      'assistant',
      '<script>alert(1)</script>\n\n<img src=x onerror=alert(1)>',
    )

    expect(wrapper.find('script').exists()).toBe(false)
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('[onerror]').exists()).toBe(false)
  })
})
