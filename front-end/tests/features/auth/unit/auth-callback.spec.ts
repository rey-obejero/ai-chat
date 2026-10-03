import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import AuthCallbackView from '@/features/auth/views/AuthCallbackView.vue'

const signInAndUp = vi.fn()

vi.mock('supertokens-web-js/recipe/thirdparty', () => ({
  default: { signInAndUp: () => signInAndUp() },
}))

vi.mock('@/features/auth/stores/session', () => ({
  useSessionStore: () => ({ refresh: vi.fn() }),
}))

const Blank = { template: '<div />' }

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/authentication/callback', name: 'auth-callback', component: Blank },
      { path: '/authentication/sign-in', name: 'sign-in', component: Blank },
      { path: '/application/conversations/:id?', name: 'conversations', component: Blank },
    ],
  })
}

async function mountCallback(query: Record<string, string> = {}) {
  const router = makeRouter()
  router.push({ name: 'auth-callback', query })
  await router.isReady()
  const wrapper = mount(AuthCallbackView, {
    global: { plugins: [router, setActivePinia(createPinia())] },
  })
  await flushPromises()
  return { wrapper, router }
}

describe('AuthCallbackView', () => {
  beforeEach(() => signInAndUp.mockReset())

  it('lands on the conversations route by default', async () => {
    signInAndUp.mockResolvedValue({ status: 'OK' })
    const { router } = await mountCallback()

    expect(router.currentRoute.value.name).toBe('conversations')
  })

  it('returns the user to the requested URL', async () => {
    signInAndUp.mockResolvedValue({ status: 'OK' })
    const { router } = await mountCallback({ redirectTo: '/application/conversations/abc' })

    expect(router.currentRoute.value.fullPath).toBe('/application/conversations/abc')
  })

  // The dangerous case: the value survived a round trip through a URL the
  // provider redirected to, so it is attacker-controllable.
  it('refuses a protocol-relative redirectTo', async () => {
    signInAndUp.mockResolvedValue({ status: 'OK' })
    const { router } = await mountCallback({ redirectTo: '//evil.example' })

    expect(router.currentRoute.value.name).toBe('conversations')
    expect(router.currentRoute.value.fullPath).not.toContain('evil.example')
  })

  it('says an existing account needs password sign-in, not "no email"', async () => {
    signInAndUp.mockResolvedValue({
      status: 'SIGN_IN_UP_NOT_ALLOWED',
      reason: 'EMAIL_ALREADY_EXISTS',
    })
    const { wrapper } = await mountCallback()

    expect(wrapper.text()).toContain('already has an account')
    expect(wrapper.text()).not.toContain('did not share an email')
  })

  it('keeps redirectTo on the link back to sign-in', async () => {
    signInAndUp.mockResolvedValue({ status: 'SIGN_IN_UP_NOT_ALLOWED', reason: 'X' })
    const { wrapper } = await mountCallback({ redirectTo: '/application/conversations/abc' })

    // Asserted by parsing rather than by substring: `/` is legal unencoded in a
    // query value, so the exact spelling is not the contract — surviving the
    // trip through the href is.
    const href = wrapper.get('a').attributes('href') ?? ''
    const target = href.slice(0, href.indexOf('?'))

    expect(target).toBe('/authentication/sign-in')
    expect(new URL(href, 'http://test').searchParams.get('redirectTo')).toBe(
      '/application/conversations/abc',
    )
  })

  it('only blames the provider when it shared no email', async () => {
    signInAndUp.mockResolvedValue({ status: 'NO_EMAIL_GIVEN_BY_PROVIDER' })
    const { wrapper } = await mountCallback()

    expect(wrapper.text()).toContain('did not share an email')
  })

  it('treats a thrown error as retryable rather than final', async () => {
    signInAndUp.mockRejectedValue(new Error('network'))
    const { wrapper } = await mountCallback()

    expect(wrapper.text()).toContain('try again')
  })

  it('never renders the provider-supplied reason', async () => {
    signInAndUp.mockResolvedValue({
      status: 'SIGN_IN_UP_NOT_ALLOWED',
      reason: '<script>alert(1)</script>',
    })
    const { wrapper } = await mountCallback()

    expect(wrapper.text()).not.toContain('script')
  })
})
