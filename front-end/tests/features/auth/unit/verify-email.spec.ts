import { flushPromises, mount } from '@vue/test-utils'
import EmailVerification from 'supertokens-web-js/recipe/emailverification'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { needsVerification, VerificationNudge, VerifyEmailView } from '@/features/auth'
import { ApiError } from '@/lib/api'

vi.mock('supertokens-web-js/recipe/emailverification', () => ({
  default: {
    verifyEmail: vi.fn(),
    sendVerificationEmail: vi.fn(),
    getEmailVerificationTokenFromURL: vi.fn(),
  },
}))

const verify = vi.mocked(EmailVerification.verifyEmail)
const send = vi.mocked(EmailVerification.sendVerificationEmail)
const readToken = vi.mocked(EmailVerification.getEmailVerificationTokenFromURL)

const Blank = { template: '<div />' }

/** PrimeVue's own label handling is not what these tests are about; the text is. */
const Button = {
  props: { label: { type: String, default: '' }, loading: Boolean },
  emits: ['click'],
  template: `<button type="button" :disabled="loading" @click="$emit('click')">{{ label }}</button>`,
}

const NUDGE_COPY = 'Verify your email to unlock the full allowance'
const QUOTA_COPY = 'You have used your token quota for this period'

function setUrl(query: string): void {
  window.history.replaceState({}, '', `/authentication/verify-email${query}`)
}

async function mountView() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/authentication/verify-email', name: 'verify-email', component: Blank },
      { path: '/authentication/sign-in', name: 'sign-in', component: Blank },
      { path: '/application/conversations', name: 'conversations', component: Blank },
    ],
  })
  router.push({ name: 'verify-email' })
  await router.isReady()

  const wrapper = mount(VerifyEmailView, {
    global: { plugins: [router], stubs: { Button } },
  })
  await flushPromises()
  return wrapper
}

function mountNudge() {
  return mount(VerificationNudge, { global: { stubs: { Button } } })
}

describe('VerifyEmailView', () => {
  beforeEach(() => {
    verify.mockReset()
    send.mockReset()
    readToken.mockReset()
    readToken.mockReturnValue('tok')
    setUrl('?token=tok&tenantId=public')
  })

  it('follows the emailed link on load and reports the address verified', async () => {
    verify.mockResolvedValue({ status: 'OK' } as never)

    const wrapper = await mountView()

    expect(verify).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('Email verified')
    expect(wrapper.text()).toContain('Your email address is verified')
  })

  it('reports an expired link', async () => {
    verify.mockResolvedValue({ status: 'EMAIL_VERIFICATION_INVALID_TOKEN_ERROR' } as never)

    const wrapper = await mountView()

    expect(wrapper.text()).toContain('This verification link is invalid or has expired.')
    expect(wrapper.text()).not.toContain('Your email address is verified')
  })

  // A request that never came back is not evidence that the link expired.
  it('reports a failure that is not a refusal', async () => {
    verify.mockRejectedValue(new Error('network'))

    const wrapper = await mountView()

    expect(wrapper.text()).toContain('Something went wrong. Please try again.')
    expect(wrapper.text()).not.toContain('invalid or has expired')
  })

  // The token is a bearer secret: it must leave the address bar as soon as the
  // page can read it (ADR-0031).
  it('strips the token from the URL on mount', async () => {
    verify.mockResolvedValue({ status: 'OK' } as never)

    await mountView()

    expect(window.location.search).not.toContain('token')
    // The non-secret tenant id is left alone.
    expect(window.location.search).toContain('tenantId=public')
  })

  it('re-injects the stripped token into the verify request', async () => {
    verify.mockResolvedValue({ status: 'OK' } as never)
    await mountView()

    const hook = verify.mock.calls[0][0]?.options?.preAPIHook
    expect(hook).toBeDefined()

    const result = await hook!({
      url: '/api/auth/public/user/email/verify',
      requestInit: { body: JSON.stringify({ method: 'token', token: '' }) },
      userContext: {},
    })

    expect(JSON.parse(result.requestInit.body as string).token).toBe('tok')
  })
})

describe('VerificationNudge', () => {
  beforeEach(() => send.mockReset())

  it('offers the verification copy and a resend instead of the quota copy', () => {
    const wrapper = mountNudge()

    expect(wrapper.text()).toContain(NUDGE_COPY)
    expect(wrapper.text()).toContain('Resend verification email')
    expect(wrapper.text()).not.toContain(QUOTA_COPY)
  })

  it('reports that the mail went out', async () => {
    send.mockResolvedValue({ status: 'OK' } as never)
    const wrapper = mountNudge()

    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(send).toHaveBeenCalledTimes(1)
    expect(wrapper.find('[role="status"]').text()).toContain(
      'Verification email sent. Check your inbox.',
    )
  })

  it('reports a resend that failed', async () => {
    send.mockRejectedValue(new Error('offline'))
    const wrapper = mountNudge()

    await wrapper.find('button').trigger('click')
    await flushPromises()

    // Announced rather than dropped: a failed resend must not look like a sent one.
    const alerts = wrapper.findAll('[role="alert"]').map((node) => node.text())
    expect(alerts).toContain('Could not send the verification email. Try again.')
  })

  it('says so when the address has already been verified', async () => {
    send.mockResolvedValue({ status: 'EMAIL_ALREADY_VERIFIED_ERROR' } as never)
    const wrapper = mountNudge()

    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Your email is already verified.')
  })
})

describe('needsVerification', () => {
  function problem(code: string, verificationRequired: boolean): ApiError {
    return new ApiError({
      type: 'about:blank',
      title: 'Too Many Requests',
      status: 429,
      code,
      verification_required: verificationRequired,
    })
  }

  it('recognises the unverified-allowance block', () => {
    expect(needsVerification(problem('QUOTA_EXCEEDED', true))).toBe(true)
  })

  it('leaves the ordinary quota block to the quota copy', () => {
    expect(needsVerification(problem('QUOTA_EXCEEDED', false))).toBe(false)
  })

  it('ignores anything else', () => {
    expect(needsVerification(problem('RATE_LIMITED', true))).toBe(false)
    expect(needsVerification(new Error('boom'))).toBe(false)
    expect(needsVerification(undefined)).toBe(false)
  })
})
