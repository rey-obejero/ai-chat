import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import SignInView from '@/features/auth/views/SignInView.vue'
import { listSocialProviders } from '@/features/auth/api'

vi.mock('@/features/auth/api', () => ({
  listSocialProviders: vi.fn(),
  getMe: vi.fn(),
}))

vi.mock('supertokens-web-js/recipe/emailpassword', () => ({
  default: { signIn: vi.fn() },
}))

vi.mock('@/features/auth/stores/session', () => ({
  useSessionStore: () => ({ refresh: vi.fn(), isAuthenticated: false, ready: true }),
}))

const mocked = vi.mocked(listSocialProviders)

const Blank = { template: '<div />' }

async function mountSignIn(query: Record<string, string> = {}) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/authentication/sign-in', name: 'sign-in', component: Blank },
      { path: '/authentication/sign-up', name: 'sign-up', component: Blank },
      { path: '/authentication/forgot-password', name: 'forgot-password', component: Blank },
      { path: '/application/conversations/:id?', name: 'conversations', component: Blank },
    ],
  })
  router.push({ name: 'sign-in', query })
  await router.isReady()

  const wrapper = mount(SignInView, {
    global: {
      plugins: [router, createPinia()],
      stubs: {
        Button: { template: '<button><slot /></button>' },
        InputText: { template: '<input />' },
        Password: { template: '<input />' },
      },
    },
  })
  await flushPromises()
  return wrapper
}

describe('SignInView', () => {
  beforeEach(() => mocked.mockReset())

  // The regression this exists for: the "or" used to live in this view rather
  // than in SocialButtons, so an unconfigured deployment rendered a divider
  // separating the form from nothing. Mounting the component alone missed it.
  it('renders no "or" divider when nothing is configured', async () => {
    mocked.mockResolvedValue([])
    const wrapper = await mountSignIn()

    expect(wrapper.findAll('p').filter((p) => p.text() === 'or')).toHaveLength(0)
  })

  it('renders the divider once there is a provider to separate', async () => {
    mocked.mockResolvedValue([{ id: 'google', name: 'Google' }])
    const wrapper = await mountSignIn()

    expect(wrapper.findAll('p').filter((p) => p.text() === 'or')).toHaveLength(1)
    expect(wrapper.text()).toContain('Continue with Google')
  })

  // The link used to render as a button with no handler, so it did nothing.
  it('links to the forgot-password route', async () => {
    mocked.mockResolvedValue([])
    const wrapper = await mountSignIn()

    const link = wrapper.findAll('a').find((a) => a.text().includes('Forgot password?'))

    expect(link?.attributes('href')).toBe('/authentication/forgot-password')
  })

  it('confirms a completed reset', async () => {
    mocked.mockResolvedValue([])
    const wrapper = await mountSignIn({ reset: 'success' })

    expect(wrapper.text()).toContain('Your password has been reset')
  })
})
