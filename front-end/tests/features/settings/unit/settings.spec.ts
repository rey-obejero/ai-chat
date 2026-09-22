import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { describe, expect, it } from 'vitest'
import { defineComponent } from 'vue'

import ApiKeyField from '@/features/settings/components/ApiKeyField.vue'
import ProviderSection from '@/features/settings/components/ProviderSection.vue'
import SettingsDialog from '@/features/settings/components/SettingsDialog.vue'

const RadioButtonStub = defineComponent({
  name: 'RadioButton',
  props: { modelValue: String, value: String, inputId: String },
  emits: ['update:modelValue'],
  template:
    '<input type="radio" :id="inputId" :value="value" :checked="modelValue === value" @change="$emit(\'update:modelValue\', value)" />',
})

const ButtonStub = defineComponent({
  props: { label: String, disabled: Boolean },
  template: '<button :disabled="disabled">{{ label }}</button>',
})

function mountProvider() {
  return mount(ProviderSection, {
    global: {
      stubs: {
        RadioButton: RadioButtonStub,
        InputText: { template: '<input />' },
        Button: ButtonStub,
      },
    },
  })
}

describe('SettingsDialog', () => {
  it('renders the Usage and Provider sections', () => {
    const wrapper = mount(SettingsDialog, {
      props: { modelValue: true },
      global: {
        plugins: [createPinia()],
        stubs: {
          Dialog: { template: '<div><slot /></div>' },
          UsagePanel: true,
          ProviderSection: true,
        },
      },
    })

    expect(wrapper.text()).toContain('Usage')
    expect(wrapper.text()).toContain('Provider')
    expect(wrapper.find('usage-panel-stub').exists()).toBe(true)
    expect(wrapper.find('provider-section-stub').exists()).toBe(true)
  })
})

describe('ProviderSection', () => {
  it('defaults to the server-provided model', () => {
    const wrapper = mountProvider()

    expect(wrapper.text()).toContain('AI Chat (server-provided)')
    expect((wrapper.find('#provider-server').element as HTMLInputElement).checked).toBe(true)
    expect(wrapper.findComponent(ApiKeyField).exists()).toBe(false)
  })

  it('reveals the key field when a personal key is chosen', async () => {
    const wrapper = mountProvider()

    await wrapper.find('#provider-byok').setValue()

    expect(wrapper.findComponent(ApiKeyField).exists()).toBe(true)
  })
})

describe('ApiKeyField', () => {
  it('shows the key input with saving disabled', () => {
    const wrapper = mount(ApiKeyField, {
      global: { stubs: { InputText: { template: '<input />' }, Button: ButtonStub } },
    })

    const button = wrapper.find('button')
    expect(button.text()).toBe('Save key')
    expect(button.attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('Not wired up yet')
  })
})
