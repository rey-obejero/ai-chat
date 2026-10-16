import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, type PropType } from 'vue'

import { ApiError } from '@/lib/api'
import { INSTRUCTIONS_MAX_LENGTH } from '@/lib/preferences'
import PersonalizationSection from '@/features/settings/components/PersonalizationSection.vue'
import { updatePreferences } from '@/features/settings/api'

vi.mock('@/features/settings/api', () => ({ updatePreferences: vi.fn() }))

/** The session the form reads the stored values from and refreshes after a save. */
const auth = vi.hoisted(() => ({ user: null as unknown, refresh: vi.fn(async () => {}) }))
vi.mock('@/features/auth', () => ({ useSessionStore: () => auth }))

/** A select that behaves like one without PrimeVue's overlay to click through. */
const SelectStub = defineComponent({
  props: {
    modelValue: String,
    inputId: String,
    options: { type: Array as PropType<{ value: string; label: string }[]>, default: () => [] },
  },
  emits: ['update:modelValue'],
  template: `<select :id="inputId" :value="modelValue" @change="$emit('update:modelValue', $event.target.value)">
    <option v-for="option in options" :key="option.value" :value="option.value">{{ option.label }}</option>
  </select>`,
})

const updateMock = vi.mocked(updatePreferences)

function mountForm(): VueWrapper {
  return mount(PersonalizationSection, {
    global: { plugins: [PrimeVue], stubs: { Select: SelectStub } },
  })
}

/** The textarea's live value, which is what the cap has to hold. */
function fieldValue(wrapper: VueWrapper): string {
  return (wrapper.find('textarea').element as HTMLTextAreaElement).value
}

beforeEach(() => {
  auth.user = {
    id: 'u1',
    email: 'ada@example.com',
    created_at: '2026-01-01T00:00:00Z',
    instructions: 'Be brief.',
    response_style: 'concise',
  }
})

describe('PersonalizationSection', () => {
  it('opens on the stored values and counts the instructions', () => {
    const wrapper = mountForm()

    expect(fieldValue(wrapper)).toBe('Be brief.')
    expect(wrapper.find('#personalization-counter').text()).toBe('9/2000')
    expect((wrapper.find('#personalization-style').element as HTMLSelectElement).value).toBe(
      'concise',
    )
  })

  it('offers the five response styles', () => {
    const wrapper = mountForm()

    expect(wrapper.findAll('#personalization-style option').map((option) => option.text())).toEqual(
      ['Default', 'Concise', 'Detailed', 'Formal', 'Casual'],
    )
  })

  it('stops the instructions at the cap the API enforces', async () => {
    const wrapper = mountForm()

    await wrapper.find('textarea').setValue('x'.repeat(INSTRUCTIONS_MAX_LENGTH + 100))
    await flushPromises()

    expect(fieldValue(wrapper)).toHaveLength(INSTRUCTIONS_MAX_LENGTH)
    expect(wrapper.find('#personalization-counter').text()).toBe('2000/2000')
  })

  it('keeps Save disabled until the form differs from what is stored', async () => {
    const wrapper = mountForm()

    expect(wrapper.find('button').attributes('disabled')).toBeDefined()

    await wrapper.find('textarea').setValue('Be brief. Be kind.')

    expect(wrapper.find('button').attributes('disabled')).toBeUndefined()
  })

  it('saves the trimmed instructions and the chosen style, then reads the user back', async () => {
    updateMock.mockResolvedValue(undefined)
    const wrapper = mountForm()

    await wrapper.find('textarea').setValue('  Be brief.  ')
    await wrapper.find('#personalization-style').setValue('formal')
    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(updateMock).toHaveBeenCalledWith({
      instructions: 'Be brief.',
      response_style: 'formal',
    })
    expect(auth.refresh).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Saved.')
  })

  it('surfaces the validation error the API returns', async () => {
    updateMock.mockRejectedValue(
      new ApiError({
        type: 'about:blank',
        title: 'Unprocessable Entity',
        status: 422,
        detail: 'instructions must be at most 2000 characters',
        code: 'VALIDATION_ERROR',
      }),
    )
    const wrapper = mountForm()

    await wrapper.find('textarea').setValue('Too long')
    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(wrapper.find('[role="alert"]').text()).toBe(
      'instructions must be at most 2000 characters',
    )
    expect(wrapper.text()).not.toContain('Saved.')
  })
})
