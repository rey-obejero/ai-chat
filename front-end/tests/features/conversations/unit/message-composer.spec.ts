import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import Tooltip from 'primevue/tooltip'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import MessageComposer from '@/features/conversations/components/MessageComposer.vue'
import { COMMANDS, commandOptionId } from '@/features/conversations/commands'

const mounted: VueWrapper[] = []

/**
 * Attached to the body so the composer's focus return is observable; the text
 * field starts empty, as it does in the view.
 */
function mountComposer(): VueWrapper {
  const wrapper = mount(MessageComposer, {
    props: { modelValue: '', disabled: false, busy: false },
    attachTo: document.body,
    global: { plugins: [PrimeVue], directives: { tooltip: Tooltip } },
  })
  mounted.push(wrapper)
  return wrapper
}

beforeEach(() => {
  // The composer's Textarea auto-resizes, and PrimeVue watches that size; jsdom
  // ships no ResizeObserver for it to construct.
  vi.stubGlobal(
    'ResizeObserver',
    class {
      observe = vi.fn()
      unobserve = vi.fn()
      disconnect = vi.fn()
    },
  )
})

afterEach(() => {
  mounted.forEach((wrapper) => wrapper.unmount())
  mounted.length = 0
})

/** The draft the composer last handed its parent. */
function draftOf(wrapper: VueWrapper): string {
  const updates = wrapper.emitted('update:modelValue') ?? []
  const last = updates[updates.length - 1]
  return last === undefined ? '' : String(last[0])
}

/** The rendered row ids, in order — the same strings `aria-activedescendant` names. */
function rowIds(wrapper: VueWrapper): (string | undefined)[] {
  return wrapper.findAll('[role="option"]').map((row) => row.attributes('id'))
}

describe('MessageComposer command palette', () => {
  it('opens on a leading slash and lists every command', async () => {
    const wrapper = mountComposer()
    const textarea = wrapper.find('textarea')

    expect(wrapper.find('[role="listbox"]').exists()).toBe(false)

    await textarea.setValue('/')

    expect(rowIds(wrapper)).toEqual(COMMANDS.map(commandOptionId))
    expect(textarea.attributes('aria-controls')).toBe('command-palette')
    expect(textarea.attributes('aria-activedescendant')).toBe(commandOptionId(COMMANDS[0]))
  })

  it('filters as the user types after the slash, case-insensitively', async () => {
    const wrapper = mountComposer()
    const textarea = wrapper.find('textarea')

    await textarea.setValue('/sum')
    expect(rowIds(wrapper)).toEqual([commandOptionId(COMMANDS[1])])

    await textarea.setValue('/TRANS')
    expect(rowIds(wrapper)).toEqual([commandOptionId(COMMANDS[3])])
  })

  it('moves the highlight with the arrow keys and wraps at either end', async () => {
    const wrapper = mountComposer()
    const textarea = wrapper.find('textarea')

    await textarea.setValue('/')

    await textarea.trigger('keydown', { key: 'ArrowDown' })
    expect(textarea.attributes('aria-activedescendant')).toBe(commandOptionId(COMMANDS[1]))

    await textarea.trigger('keydown', { key: 'ArrowUp' })
    await textarea.trigger('keydown', { key: 'ArrowUp' })
    expect(textarea.attributes('aria-activedescendant')).toBe(commandOptionId(COMMANDS[3]))

    const highlighted = wrapper
      .findAll('[role="option"]')
      .filter((row) => row.attributes('aria-selected') === 'true')
    expect(highlighted).toHaveLength(1)
  })

  it('inserts the highlighted template on Enter and sends nothing', async () => {
    const wrapper = mountComposer()
    const textarea = wrapper.find('textarea')

    await textarea.setValue('/')
    await textarea.trigger('keydown', { key: 'ArrowDown' })
    await textarea.trigger('keydown', { key: 'Enter' })
    await flushPromises()

    expect(draftOf(wrapper)).toBe(COMMANDS[1].template)
    expect(wrapper.emitted('submit')).toBeUndefined()
    expect(wrapper.find('[role="listbox"]').exists()).toBe(false)
    expect(document.activeElement).toBe(textarea.element)
  })

  it('keeps the text that followed the filter when it inserts', async () => {
    const wrapper = mountComposer()
    const textarea = wrapper.find('textarea')

    await textarea.setValue('/trans hello')
    await textarea.trigger('keydown', { key: 'Enter' })

    expect(draftOf(wrapper)).toBe('Translate the following into English:\n\nhello')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('inserts with Tab as well as Enter', async () => {
    const wrapper = mountComposer()
    const textarea = wrapper.find('textarea')

    await textarea.setValue('/rew')
    await textarea.trigger('keydown', { key: 'Tab' })

    expect(draftOf(wrapper)).toBe(COMMANDS[2].template)
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('inserts the clicked command', async () => {
    const wrapper = mountComposer()
    const textarea = wrapper.find('textarea')

    await textarea.setValue('/')
    await wrapper.findAll('[role="option"]')[1].trigger('click')

    expect(draftOf(wrapper)).toBe(COMMANDS[1].template)
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('dismisses on Escape without touching the draft', async () => {
    const wrapper = mountComposer()
    const textarea = wrapper.find('textarea')

    await textarea.setValue('/sum')
    await textarea.trigger('keydown', { key: 'Escape' })

    expect(wrapper.find('[role="listbox"]').exists()).toBe(false)
    expect(draftOf(wrapper)).toBe('/sum')
    expect(wrapper.emitted('submit')).toBeUndefined()

    // Typing a different filter brings the palette back.
    await textarea.setValue('/summ')
    expect(wrapper.find('[role="listbox"]').exists()).toBe(true)
  })

  it('closes as soon as the draft no longer starts with the slash', async () => {
    const wrapper = mountComposer()
    const textarea = wrapper.find('textarea')

    await textarea.setValue('/')
    expect(wrapper.find('[role="listbox"]').exists()).toBe(true)

    await textarea.setValue('')
    expect(wrapper.find('[role="listbox"]').exists()).toBe(false)
  })

  it('ignores a slash that is not leading', async () => {
    const wrapper = mountComposer()
    const textarea = wrapper.find('textarea')

    await textarea.setValue('see /api/v1')
    expect(wrapper.find('[role="listbox"]').exists()).toBe(false)

    await textarea.trigger('keydown', { key: 'Enter' })
    expect(wrapper.emitted('submit')).toHaveLength(1)
  })

  it('states an empty filter result and still refuses to send', async () => {
    const wrapper = mountComposer()
    const textarea = wrapper.find('textarea')

    await textarea.setValue('/zzz')
    expect(wrapper.find('[role="status"]').text()).toBe('No matching commands.')

    await textarea.trigger('keydown', { key: 'Enter' })

    expect(wrapper.emitted('submit')).toBeUndefined()
    expect(draftOf(wrapper)).toBe('/zzz')
  })

  it('still sends an ordinary draft on Enter', async () => {
    const wrapper = mountComposer()
    const textarea = wrapper.find('textarea')

    await textarea.setValue('hello')
    await textarea.trigger('keydown', { key: 'Enter' })

    expect(wrapper.emitted('submit')).toHaveLength(1)
  })
})
