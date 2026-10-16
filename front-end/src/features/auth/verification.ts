import EmailVerification from 'supertokens-web-js/recipe/emailverification'

import { ApiError } from '@/lib/api'

/**
 * The copy shown in place of the plain quota message when the reduced allowance
 * refused the request (ADR-0039). It names the way out — verifying — because
 * waiting for the period to reset is not the only one.
 */
export const VERIFICATION_NUDGE_COPY =
  'You have used the token allowance for unverified accounts. Verify your email to unlock the full allowance.'

/** How a resend ended: the mail went out, there was nothing to send, or it did not. */
export type ResendOutcome = 'sent' | 'already-verified' | 'failed'

/** The line a resend reports each outcome with. */
export const RESEND_MESSAGE: Record<ResendOutcome, string> = {
  sent: 'Verification email sent. Check your inbox.',
  'already-verified': 'Your email is already verified.',
  failed: 'Could not send the verification email. Try again.',
}

/**
 * Whether a refused request is the unverified-allowance block rather than the
 * ordinary quota block: the same quota problem, carrying the flag that says
 * verifying would lift it (ADR-0039).
 */
export function needsVerification(error: unknown): boolean {
  return error instanceof ApiError && error.code === 'QUOTA_EXCEEDED' && error.verificationRequired
}

/**
 * Ask SuperTokens to send the verification mail again (FR-4). The recipe owns
 * the message, so this reports only how the ask ended — an address that is
 * already verified is a different answer from a failure, and each says so.
 */
export async function resendVerificationEmail(): Promise<ResendOutcome> {
  try {
    const response = await EmailVerification.sendVerificationEmail()

    if (response.status === 'OK') {
      return 'sent'
    }
    if (response.status === 'EMAIL_ALREADY_VERIFIED_ERROR') {
      return 'already-verified'
    }
    return 'failed'
  } catch {
    return 'failed'
  }
}
