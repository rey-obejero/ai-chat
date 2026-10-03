import { flushPromises, mount } from '@vue/test-utils'
import EmailPassword from 'supertokens-web-js/recipe/emailpassword'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import ResetPasswordView from '@/features/auth/views/ResetPasswordView.vue'

vi.mock('supertokens-web-js/recipe/emailpassword', () => ({
  default: {
    submitNewPassword: vi.fn(),
    getResetPasswordTokenFromURL: vi.fn(),
  },
}))

const submit = vi.mocked(EmailPassword.submitNewPassword)
const readToken = vi.mocked(EmailPassword.getResetPasswordTokenFromURL)

const Blank = { template: '<div />' }

const Password = {
  props: ['modelValue'],
  emits: ['update:modelValue'],
  template: `<input :value="modelValue" @input="$emit('update:modelValue', $event.target.value)" />`,
}

function setUrl(query: string) {
  window.history.replaceState({}, '', `/authentication/reset-password${query}`)
}

async function mountView() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/authentication/reset-password', name: 'reset-password', component: Blank },
      { path: '/authentication/sign-in', name: 'sign-in', component: Blank },
      { path: '/authentication/forgot-password', name: 'forgot-password', component: Blank },
    ],
  })
  router.push({ name: 'reset-password' })
  await router.isReady()

  const wrapper = mount(ResetPasswordView, {
    global: {
      plugins: [router],
      stubs: { Button: { template: '<button><slot /></button>' }, Password },
    },
  })
  await flushPromises()
  return { wrapper, router }
}

describe('ResetPasswordView', () => {
  beforeEach(() => {
    submit.mockReset()
    readToken.mockReset()
    readToken.mockReturnValue('tok')
    setUrl('?token=tok&tenantId=public')
  })

  it('offers a fresh request when the token is missing', async () => {
    readToken.mockReturnValue('')
    setUrl('')

    const { wrapper } = await mountView()

    expect(wrapper.text()).toContain('missing its token')
    expect(wrapper.text()).toContain('Request a new link')
    expect(wrapper.find('form').exists()).toBe(false)
  })

  // The token is a bearer secret: it must leave the address bar as soon as the
  // page can read it, not sit there until submit (ADR-0031).
  it('strips the token from the URL on mount', async () => {
    await mountView()

    expect(window.location.search).not.toContain('token')
    // The non-secret tenant id is left alone.
    expect(window.location.search).toContain('tenantId=public')
  })

  it('re-injects the stripped token into the submit request', async () => {
    submit.mockResolvedValue({ status: 'OK' } as never)
    const { wrapper } = await mountView()

    await wrapper.find('input').setValue('new-password')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const hook = submit.mock.calls[0][0].options?.preAPIHook
    expect(hook).toBeDefined()

    const result = await hook!({
      url: '/api/auth/public/user/password/reset',
      requestInit: { body: JSON.stringify({ token: '', method: 'token' }) },
      userContext: {},
    })

    expect(JSON.parse(result.requestInit.body as string).token).toBe('tok')
  })

  it('sends the user to sign in after a successful reset', async () => {
    // A reset creates no session, so there is nowhere else to go.
    submit.mockResolvedValue({ status: 'OK' } as never)
    const { wrapper, router } = await mountView()

    await wrapper.find('input').setValue('new-password')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(router.currentRoute.value.name).toBe('sign-in')
    expect(router.currentRoute.value.query.reset).toBe('success')
  })

  it('reports an invalid or reused token and offers a new link', async () => {
    submit.mockResolvedValue({ status: 'RESET_PASSWORD_INVALID_TOKEN_ERROR' } as never)
    const { wrapper } = await mountView()

    await wrapper.find('input').setValue('new-password')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('invalid or has expired')
    expect(wrapper.text()).toContain('Request a new link')
  })
})
