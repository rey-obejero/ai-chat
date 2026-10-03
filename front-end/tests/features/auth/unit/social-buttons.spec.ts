import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import SocialButtons from '@/features/auth/components/SocialButtons.vue'
import { listSocialProviders } from '@/features/auth/api'
import { router } from '@/app/router'

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

function mountButtons() {
  return mount(SocialButtons, {
    global: { plugins: [router] },
  })
}

describe('SocialButtons', () => {
  it('renders nothing at all when no providers are configured', async () => {
    // Including the divider: it moved into this component precisely so one
    // condition could hide both.
    mocked.mockResolvedValue([])
    const wrapper = mountButtons()
    await flushPromises()

    expect(wrapper.find('button').exists()).toBe(false)
    expect(wrapper.text()).toBe('')
  })

  it('renders the name the backend supplies', async () => {
    mocked.mockResolvedValue([{ id: 'github', name: 'GitHub' }])
    const wrapper = mountButtons()
    await flushPromises()

    const labels = wrapper.findAll('button').map((b) => b.text())
    expect(labels).toHaveLength(1)
    expect(labels[0]).toContain('Continue with GitHub')
  })

  it('renders a provider it has no brand artwork for', async () => {
    // The bug this guards: an unrecognised provider used to be dropped from the
    // list, so a deployment that configured one showed no social option at all
    // and gave the user no hint that anything was meant to be there.
    mocked.mockResolvedValue([{ id: 'okta', name: 'Okta' }])
    const wrapper = mountButtons()
    await flushPromises()

    const buttons = wrapper.findAll('button')
    expect(buttons).toHaveLength(1)
    expect(buttons[0]!.text()).toContain('Continue with Okta')
  })

  it('shows no icon for a provider it has no mark for', async () => {
    // A stand-in icon would be inventing branding we do not have.
    mocked.mockResolvedValue([{ id: 'okta', name: 'Okta' }])
    const wrapper = mountButtons()
    await flushPromises()

    expect(wrapper.find('svg').exists()).toBe(false)
  })

  it('still shows its icon for a provider it knows', async () => {
    mocked.mockResolvedValue([{ id: 'github', name: 'GitHub' }])
    const wrapper = mountButtons()
    await flushPromises()

    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('re-enables the buttons when the hand-off to the provider never happens', async () => {
    // jsdom refuses to navigate and prints "Not implemented: navigation" to
    // stderr. That is the scenario under test — the page stays put — so the
    // message is expected output, not a failure.
    mocked.mockResolvedValue([{ id: 'github', name: 'GitHub' }])
    authorisationUrl.mockResolvedValue('https://github.example/authorize')
    const wrapper = mountButtons()
    await flushPromises()

    await wrapper.get('button').trigger('click')
    await flushPromises()

    expect(wrapper.get('button').attributes('disabled')).toBeUndefined()
  })

  it('reports a failed lookup instead of rendering dead buttons', async () => {
    mocked.mockRejectedValue(new Error('offline'))
    const wrapper = mountButtons()
    await flushPromises()

    expect(wrapper.find('button').exists()).toBe(false)
    expect(wrapper.get('[role="alert"]').text()).toContain('unavailable')
  })
})
