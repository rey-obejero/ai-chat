import { flushPromises, mount, type DOMWrapper, type VueWrapper } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import ProfileSection from '@/features/settings/components/ProfileSection.vue'
import { ApiError } from '@/lib/api'
import { DISPLAY_NAME_MAX_LENGTH } from '@/lib/display-name'

/** The session whose user the section shows and whose name it saves. */
const auth = vi.hoisted(() => ({
  user: null as unknown,
  saveDisplayName: vi.fn(async () => {}),
}))
vi.mock('@/features/auth', () => ({ useSessionStore: () => auth }))

function mountSection(): VueWrapper {
  return mount(ProfileSection, { global: { plugins: [PrimeVue] } })
}

/** The field's live value, which is what the stored name has to reach. */
function fieldValue(wrapper: VueWrapper): string {
  return (wrapper.find('#profile-name').element as HTMLInputElement).value
}

function saveButton(wrapper: VueWrapper): DOMWrapper<Element> {
  return wrapper.find('button')
}

beforeEach(() => {
  auth.user = {
    id: 'u1',
    email: 'ada@example.com',
    created_at: '2026-01-01T00:00:00Z',
    display_name: 'Ada Lovelace',
    name_prompt_seen: true,
    instructions: null,
    response_style: 'default',
  }
  auth.saveDisplayName = vi.fn(async () => {})
})

describe('ProfileSection', () => {
  it('opens on the stored name', () => {
    expect(fieldValue(mountSection())).toBe('Ada Lovelace')
  })

  it('keeps Save disabled until the name differs from what is stored', async () => {
    const wrapper = mountSection()

    expect(saveButton(wrapper).attributes('disabled')).toBeDefined()

    await wrapper.find('#profile-name').setValue('Ada L.')

    expect(saveButton(wrapper).attributes('disabled')).toBeUndefined()
  })

  it('saves the trimmed name and confirms the write', async () => {
    const wrapper = mountSection()

    await wrapper.find('#profile-name').setValue('  Ada L.  ')
    await saveButton(wrapper).trigger('click')
    await flushPromises()

    expect(auth.saveDisplayName).toHaveBeenCalledWith('Ada L.')
    expect(fieldValue(wrapper)).toBe('Ada L.')
    expect(wrapper.text()).toContain('Saved.')
  })

  it('refuses a blank name in the field itself', async () => {
    const wrapper = mountSection()

    await wrapper.find('#profile-name').setValue('   ')
    await flushPromises()

    expect(wrapper.find('[role="alert"]').text()).toContain('A name is required')
    expect(saveButton(wrapper).attributes('disabled')).toBeDefined()
    expect(auth.saveDisplayName).not.toHaveBeenCalled()
  })

  it('surfaces the refusal the API gives for a name it will not store', async () => {
    auth.saveDisplayName = vi.fn(async () => {
      throw new ApiError({
        type: 'about:blank',
        title: 'Unprocessable Entity',
        status: 422,
        detail: 'That name is not allowed.',
        code: 'VALIDATION_ERROR',
      })
    })
    const wrapper = mountSection()

    await wrapper.find('#profile-name').setValue('a slur')
    await saveButton(wrapper).trigger('click')
    await flushPromises()

    const message = wrapper.find('[role="alert"]')
    expect(message.text()).toBe('That name is not allowed.')
    expect(message.classes()).toContain('text-danger')
  })

  it('stops the name at the cap the API enforces', async () => {
    const wrapper = mountSection()

    await wrapper.find('#profile-name').setValue('x'.repeat(DISPLAY_NAME_MAX_LENGTH + 10))
    await flushPromises()

    expect(fieldValue(wrapper)).toHaveLength(DISPLAY_NAME_MAX_LENGTH)
  })

  it('retires the refusal once the name is edited', async () => {
    auth.saveDisplayName = vi.fn(async () => {
      throw new ApiError({
        type: 'about:blank',
        title: 'Unprocessable Entity',
        status: 422,
        detail: 'That name is not allowed.',
        code: 'VALIDATION_ERROR',
      })
    })
    const wrapper = mountSection()

    await wrapper.find('#profile-name').setValue('a slur')
    await saveButton(wrapper).trigger('click')
    await flushPromises()

    await wrapper.find('#profile-name').setValue('Ada')

    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
  })
})
