import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import EmailPassword from 'supertokens-web-js/recipe/emailpassword'

import ForgotPasswordView from '@/features/auth/views/ForgotPasswordView.vue'

vi.mock('supertokens-web-js/recipe/emailpassword', () => ({
  default: { sendPasswordResetEmail: vi.fn() },
}))

const mocked = vi.mocked(EmailPassword.sendPasswordResetEmail)

const Blank = { template: '<div />' }

const InputText = {
  props: ['modelValue'],
  emits: ['update:modelValue'],
  template: `<input :value="modelValue" @input="$emit('update:modelValue', $event.target.value)" />`,
}

async function mountView() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/authentication/forgot-password', name: 'forgot-password', component: Blank },
      { path: '/authentication/sign-in', name: 'sign-in', component: Blank },
    ],
  })
  router.push({ name: 'forgot-password' })
  await router.isReady()

  const wrapper = mount(ForgotPasswordView, {
    global: {
      plugins: [router],
      stubs: { Button: { template: '<button><slot /></button>' }, InputText },
    },
  })
  await flushPromises()
  return wrapper
}

async function submitEmail(wrapper: Awaited<ReturnType<typeof mountView>>) {
  await wrapper.find('input').setValue('user@example.com')
  await wrapper.find('form').trigger('submit')
  await flushPromises()
}

const CONFIRMATION = "If that address has an account, we've sent a link"

describe('ForgotPasswordView', () => {
  beforeEach(() => mocked.mockReset())

  it('confirms generically after a successful request', async () => {
    mocked.mockResolvedValue({ status: 'OK' } as never)
    const wrapper = await mountView()

    await submitEmail(wrapper)

    expect(wrapper.text()).toContain(CONFIRMATION)
  })

  it('shows the same confirmation for PASSWORD_RESET_NOT_ALLOWED', async () => {
    // It would reveal something about the account to say anything else.
    mocked.mockResolvedValue({ status: 'PASSWORD_RESET_NOT_ALLOWED', reason: 'x' } as never)
    const wrapper = await mountView()

    await submitEmail(wrapper)

    expect(wrapper.text()).toContain(CONFIRMATION)
  })

  it('shows a field error for a malformed address and no confirmation', async () => {
    mocked.mockResolvedValue({
      status: 'FIELD_ERROR',
      formFields: [{ id: 'email', error: 'Email is invalid' }],
    } as never)
    const wrapper = await mountView()

    await submitEmail(wrapper)

    expect(wrapper.text()).toContain('Email is invalid')
    expect(wrapper.text()).not.toContain(CONFIRMATION)
  })
})
