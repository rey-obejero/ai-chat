import type { RouteLocationRaw } from 'vue-router'

/**
 * Validate a post-sign-in redirect target.
 *
 * The value is user-controllable the moment anyone can hand-craft a URL.
 * `//evil.example` is protocol-relative, and `router.push` will happily follow
 * it off-origin, so both it and any absolute URL are rejected.
 *
 * Backslashes are rejected too: browsers normalise `\` to `/`, which turns
 * `/\evil.example` into the protocol-relative form. A legitimate path should
 * carry an encoded `%5C` at most.
 *
 * Returns the path when it is a same-origin absolute path, otherwise `null`;
 * there is no legitimate case for sending a user to another host after signing
 * in.
 */
export function safeRedirectPath(value: unknown): string | null {
  if (typeof value !== 'string') return null
  if (!value.startsWith('/')) return null
  if (value.startsWith('//')) return null
  if (value.includes('\\')) return null
  return value
}

/** Validate a redirect target, falling back to a route when it is unusable. */
export function safeRedirect(value: unknown, fallback: RouteLocationRaw): RouteLocationRaw {
  return safeRedirectPath(value) ?? fallback
}

// A path, not a credential: no token or session data is ever stored here.
const REDIRECT_KEY = 'ai-chat:post-auth-redirect'

/**
 * Carry a post-sign-in destination across the provider round trip.
 *
 * It cannot ride on the callback URL. That URL is the provider's `redirect_uri`,
 * and Google and GitHub both reject one whose query does not exactly match the
 * registered URI — so `?redirectTo=…` on it fails with `redirect_uri_mismatch`.
 *
 * `sessionStorage` is per-tab, which is exactly the lifetime of an OAuth round
 * trip: the destination is set before the browser leaves and read on the
 * callback, then cleared. It is a validated path and nothing else.
 */
export function rememberRedirect(value: unknown): void {
  const target = safeRedirectPath(value)
  if (target) sessionStorage.setItem(REDIRECT_KEY, target)
}

/** Read and clear the remembered destination. */
export function takeRedirect(): string | null {
  const target = sessionStorage.getItem(REDIRECT_KEY)
  sessionStorage.removeItem(REDIRECT_KEY)
  return target
}
