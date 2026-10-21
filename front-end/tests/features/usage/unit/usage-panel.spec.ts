import { mount } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import { useSessionStore, type User } from '@/features/auth'
import { useUsageStore } from '@/features/usage'
import UsagePanel from '@/features/usage/components/UsagePanel.vue'

function mountWith(options: { limit: number; full: number; verified: boolean }) {
  const session = useSessionStore()
  // The panel reads the verified flag from the account and nothing else.
  session.user = { email_verified: options.verified } as User
  useUsageStore().usage = {
    used: 250,
    limit: options.limit,
    full_limit: options.full,
    remaining: options.limit - 250,
    period_start: '2026-09-01T00:00:00Z',
    resets_at: '2026-10-01T00:00:00Z',
  }
  return mount(UsagePanel, { global: { plugins: [PrimeVue] } })
}

beforeEach(() => setActivePinia(createPinia()))

describe('UsagePanel reduced allowance', () => {
  it('explains the reduced figure and offers to verify', () => {
    const wrapper = mountWith({ limit: 500, full: 1000, verified: false })

    // The number the panel reports is the reduced one, so it says why.
    expect(wrapper.text()).toContain("isn't verified")
    expect(wrapper.text()).toContain('500 of 1k')
    expect(wrapper.find('button').text()).toContain('Resend')
  })

  it('says nothing extra once the address is verified', () => {
    const wrapper = mountWith({ limit: 1000, full: 1000, verified: true })

    expect(wrapper.text()).not.toContain("isn't verified")
    expect(wrapper.find('button').exists()).toBe(false)
  })
})
