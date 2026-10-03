import type { RouteLocationRaw } from 'vue-router'

/**
 * Resolve a post-sign-in redirect target.
 *
 * The value arrives in the query string, which means it is user-controllable the
 * moment anyone can hand-craft a URL. `//evil.example` is protocol-relative, and
 * `router.push` will happily follow it off-origin, so both it and any absolute
 * URL are rejected in favour of the fallback.
 *
 * Backslashes are rejected too: browsers normalise `\` to `/`, which turns
 * `/\evil.example` into the protocol-relative form. A legitimate path should
 * carry an encoded `%5C` at most.
 *
 * Only same-origin absolute paths are accepted; there is no legitimate case for
 * sending a user to another host after signing in. Named routes are the right
 * fallback, which is why this returns a route location rather than a string.
 */
export function safeRedirect(value: unknown, fallback: RouteLocationRaw): RouteLocationRaw {
  if (typeof value !== 'string') return fallback
  if (!value.startsWith('/')) return fallback
  if (value.startsWith('//')) return fallback
  if (value.includes('\\')) return fallback
  return value
}
