import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import SocialButtons from '@/features/auth/components/SocialButtons.vue'
import { listSocialProviders } from '@/features/auth/api'
import { takeRedirect } from '@/lib/redirect'

vi.mock('@/features/auth/api', () => ({
  listSocialProviders: vi.fn(),
}))

const authorisationUrl = vi.fn()

vi.mock('supertokens-web-js/recipe/thirdparty', () => ({
  default: {
    getAuthorisationURLWithQueryParamsAndSetState: (...args: unknown[]) =>
      authorisationUrl(...args),
  },
}))

const mocked = vi.mocked(listSocialProviders)

const Blank = { template: '<div />' }

async function mountButtons(query: Record<string, string> = {}) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/authentication/sign-in', name: 'sign-in', component: Blank },
      { path: '/authentication/callback', name: 'auth-callback', component: Blank },
      { path: '/application/conversations/:id?', name: 'conversations', component: Blank },
    ],
  })
  router.push({ name: 'sign-in', query })
  await router.isReady()

  const wrapper = mount(SocialButtons, { global: { plugins: [router] } })
  await flushPromises()
  return wrapper
}

describe('SocialButtons', () => {
  beforeEach(() => {
    mocked.mockReset()
    authorisationUrl.mockReset()
    sessionStorage.clear()
  })

  it('renders nothing at all when no providers are configured', async () => {
    // Including the divider: it moved into this component precisely so one
    // condition could hide both.
    mocked.mockResolvedValue([])
    const wrapper = await mountButtons()

    expect(wrapper.find('button').exists()).toBe(false)
    expect(wrapper.text()).toBe('')
  })

  it('renders the name the backend supplies', async () => {
    mocked.mockResolvedValue([{ id: 'github', name: 'GitHub' }])
    const wrapper = await mountButtons()

    const labels = wrapper.findAll('button').map((b) => b.text())
    expect(labels).toHaveLength(1)
    expect(labels[0]).toContain('Continue with GitHub')
  })

  it('renders a provider it has no brand artwork for', async () => {
    // The bug this guards: an unrecognised provider used to be dropped from the
    // list, so a deployment that configured one showed no social option at all
    // and gave the user no hint that anything was meant to be there.
    mocked.mockResolvedValue([{ id: 'okta', name: 'Okta' }])
    const wrapper = await mountButtons()

    const buttons = wrapper.findAll('button')
    expect(buttons).toHaveLength(1)
    expect(buttons[0]!.text()).toContain('Continue with Okta')
  })

  it('shows no icon for a provider it has no mark for', async () => {
    // A stand-in icon would be inventing branding we do not have.
    mocked.mockResolvedValue([{ id: 'okta', name: 'Okta' }])
    const wrapper = await mountButtons()

    expect(wrapper.find('svg').exists()).toBe(false)
  })

  it('still shows its icon for a provider it knows', async () => {
    mocked.mockResolvedValue([{ id: 'github', name: 'GitHub' }])
    const wrapper = await mountButtons()

    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('re-enables the buttons when the hand-off to the provider never happens', async () => {
    // jsdom refuses to navigate and prints "Not implemented: navigation" to
    // stderr. That is the scenario under test — the page stays put — so the
    // message is expected output, not a failure.
    mocked.mockResolvedValue([{ id: 'github', name: 'GitHub' }])
    authorisationUrl.mockResolvedValue('https://github.example/authorize')
    const wrapper = await mountButtons()

    await wrapper.get('button').trigger('click')
    await flushPromises()

    expect(wrapper.get('button').attributes('disabled')).toBeUndefined()
  })

  // The bug this guards: `redirectTo` used to be appended to the callback URL,
  // so the provider received a redirect_uri with a query string and rejected it
  // with `redirect_uri_mismatch` (Google) / "not associated with this
  // application" (GitHub).
  it('hands the provider a callback URL with no query string', async () => {
    mocked.mockResolvedValue([{ id: 'github', name: 'GitHub' }])
    authorisationUrl.mockResolvedValue('https://github.example/authorize')
    const wrapper = await mountButtons({ redirectTo: '/application/conversations/abc' })

    await wrapper.get('button').trigger('click')
    await flushPromises()

    const input = authorisationUrl.mock.calls[0]![0] as { frontendRedirectURI: string }
    expect(input.frontendRedirectURI).toBe(`${window.location.origin}/authentication/callback`)
    // The destination is preserved for the callback view, just not on the URL.
    expect(takeRedirect()).toBe('/application/conversations/abc')
  })

  it('reports a failed lookup instead of rendering dead buttons', async () => {
    mocked.mockRejectedValue(new Error('offline'))
    const wrapper = await mountButtons()

    expect(wrapper.find('button').exists()).toBe(false)
    expect(wrapper.get('[role="alert"]').text()).toContain('unavailable')
  })
})
