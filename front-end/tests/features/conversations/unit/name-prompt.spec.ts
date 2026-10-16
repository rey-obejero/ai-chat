import { flushPromises, mount, type DOMWrapper, type VueWrapper } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import Dialog from 'primevue/dialog'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import NamePromptDialog from '@/features/conversations/components/NamePromptDialog.vue'
import { ApiError } from '@/lib/api'

/** The session the prompt reads the name from and writes it back through. */
const auth = vi.hoisted(() => ({
  user: null as unknown,
  saveDisplayName: vi.fn(async () => {}),
  skipNamePrompt: vi.fn(async () => {}),
}))
vi.mock('@/features/auth', () => ({ useSessionStore: () => auth }))

const mounted: VueWrapper[] = []

async function mountPrompt(): Promise<VueWrapper> {
  const wrapper = mount(NamePromptDialog, {
    // The dialog is teleported to the body; rendering it in place keeps the field
    // and its actions where the test can reach them.
    global: { plugins: [PrimeVue], stubs: { teleport: true } },
  })
  mounted.push(wrapper)
  // The dialog reaches the DOM through a Portal, which renders a tick after it
  // mounts, so the field is not there yet.
  await flushPromises()
  return wrapper
}

/** The field's live value, which is what the prefill has to hold. */
function fieldValue(wrapper: VueWrapper): string {
  return (wrapper.find('#name-prompt-name').element as HTMLInputElement).value
}

/** PrimeVue puts the label inside the button, so the text is where to look. */
function action(wrapper: VueWrapper, label: string): DOMWrapper<Element> {
  return wrapper.findAll('button').find((button) => button.text() === label)!
}

beforeEach(() => {
  auth.user = { display_name: 'Ada Lovelace', email: 'ada@example.com', name_prompt_seen: false }
  auth.saveDisplayName = vi.fn(async () => {})
  auth.skipNamePrompt = vi.fn(async () => {})
})

afterEach(() => {
  mounted.forEach((wrapper) => wrapper.unmount())
  mounted.length = 0
})

describe('NamePromptDialog', () => {
  it('opens prefilled with the name the account already has', async () => {
    expect(fieldValue(await mountPrompt())).toBe('Ada Lovelace')
  })

  it('falls back to the email when the account somehow has no name', async () => {
    auth.user = { display_name: '', email: 'ada@example.com', name_prompt_seen: false }

    expect(fieldValue(await mountPrompt())).toBe('ada@example.com')
  })

  it('saves the trimmed name, which is also what answers the prompt', async () => {
    const wrapper = await mountPrompt()

    await wrapper.find('#name-prompt-name').setValue('  Ada L.  ')
    await action(wrapper, 'Save').trigger('click')
    await flushPromises()

    expect(auth.saveDisplayName).toHaveBeenCalledWith('Ada L.')
    expect(auth.skipNamePrompt).not.toHaveBeenCalled()
  })

  it('refuses an empty name, leaving skipping as the other answer', async () => {
    const wrapper = await mountPrompt()

    await wrapper.find('#name-prompt-name').setValue('   ')
    await flushPromises()

    expect(action(wrapper, 'Save').attributes('disabled')).toBeDefined()
    expect(auth.saveDisplayName).not.toHaveBeenCalled()
  })

  it('skips without writing a name', async () => {
    const wrapper = await mountPrompt()

    await action(wrapper, 'Skip').trigger('click')
    await flushPromises()

    expect(auth.skipNamePrompt).toHaveBeenCalledWith()
    expect(auth.saveDisplayName).not.toHaveBeenCalled()
  })

  it('answers once, even if the action is pressed again while it is in flight', async () => {
    let answer: () => void = () => {}
    auth.saveDisplayName = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          answer = resolve
        }),
    )
    const wrapper = await mountPrompt()

    await action(wrapper, 'Save').trigger('click')
    await action(wrapper, 'Save').trigger('click')
    answer()
    await flushPromises()

    expect(auth.saveDisplayName).toHaveBeenCalledTimes(1)
  })

  it('offers no way out but Save and Skip', async () => {
    const wrapper = await mountPrompt()
    const dialog = wrapper.findComponent(Dialog)

    expect(dialog.props('closable')).toBe(false)
    expect(dialog.props('closeOnEscape')).toBe(false)
    expect(dialog.props('dismissableMask')).toBe(false)
    // `closable: false` renders no close control at all, so there is nothing to
    // click and nothing for Escape to be the equivalent of.
    expect(wrapper.find('.p-dialog-close-button').exists()).toBe(false)
  })

  it('stays open when Escape or the mask is used on it', async () => {
    const wrapper = await mountPrompt()

    document.dispatchEvent(new KeyboardEvent('keydown', { code: 'Escape' }))
    const mask = wrapper.find('.p-dialog-mask')
    await mask.trigger('mousedown')
    await mask.trigger('mouseup')
    await flushPromises()

    expect(wrapper.find('#name-prompt-name').exists()).toBe(true)
    expect(auth.saveDisplayName).not.toHaveBeenCalled()
    expect(auth.skipNamePrompt).not.toHaveBeenCalled()
  })

  it('states the refusal when the API rejects the name', async () => {
    auth.saveDisplayName = vi.fn(async () => {
      throw new ApiError({
        type: 'about:blank',
        title: 'Unprocessable Entity',
        status: 422,
        detail: 'That name is not allowed.',
        code: 'VALIDATION_ERROR',
      })
    })
    const wrapper = await mountPrompt()

    await action(wrapper, 'Save').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('That name is not allowed.')
  })
})
