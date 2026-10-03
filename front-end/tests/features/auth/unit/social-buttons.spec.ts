import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import SocialButtons from '@/features/auth/components/SocialButtons.vue'
import { listSocialProviders } from '@/features/auth/api'
import { router } from '@/app/router'

vi.mock('@/features/auth/api', () => ({
  listSocialProviders: vi.fn(),
}))

const mocked = vi.mocked(listSocialProviders)

function mountButtons() {
  return mount(SocialButtons, {
    global: { plugins: [router] },
  })
}

describe('SocialButtons', () => {
  it('renders nothing at all when no providers are configured', async () => {
    // Including the wrapper: a divider with nothing above it is the tell of a
    // hardcoded list.
    mocked.mockResolvedValue([])
    const wrapper = mountButtons()
    await flushPromises()

    expect(wrapper.find('button').exists()).toBe(false)
    expect(wrapper.text()).toBe('')
  })

  it('renders only the configured providers', async () => {
    mocked.mockResolvedValue(['github'])
    const wrapper = mountButtons()
    await flushPromises()

    const labels = wrapper.findAll('button').map((b) => b.text())
    expect(labels).toHaveLength(1)
    expect(labels[0]).toContain('GitHub')
  })

  it('ignores a provider it has no button for', async () => {
    mocked.mockResolvedValue(['google', 'some-future-provider'])
    const wrapper = mountButtons()
    await flushPromises()

    expect(wrapper.findAll('button')).toHaveLength(1)
    expect(wrapper.text()).toContain('Google')
  })

  it('reports a failed lookup instead of rendering dead buttons', async () => {
    mocked.mockRejectedValue(new Error('offline'))
    const wrapper = mountButtons()
    await flushPromises()

    expect(wrapper.find('button').exists()).toBe(false)
    expect(wrapper.get('[role="alert"]').text()).toContain('unavailable')
  })
})
