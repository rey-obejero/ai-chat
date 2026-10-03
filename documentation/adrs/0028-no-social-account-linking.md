# ADR-0028: Social sign-in never merges into an existing account

- **Status:** Accepted
- **Date:** 2026-10-03
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

When a social sign-in presents an email that already belongs to a password
account, the sign-in is refused and the user is sent back to password sign-in.
Identities are never merged, uniformly across every provider.

## Context

[ADR-0010](0010-supertokens-auth.md) settles *which* vendor handles
authentication. It does not say what the vendor is permitted to do with
identity — and that is the decision with the sharper edges.

The question arises because auto-linking is what most users would *want*: they
signed up with a password, then later added "Sign in with Google", and expect
one account. The temptation is to grant it silently.

## Decision

Social sign-in is **refused** when the presented email already belongs to an
existing account. The user may sign in with email/password or with the social
provider they originally used — never both, and never silently merged.

No code path in the application merges a social identity into an existing
account. `shouldTryLinkingWithSessionUser` is deliberately never passed, so it
stays `undefined` and the SDK attempts no linking.

## Consequences

- **Easier:** one rule to reason about, no per-provider matrix. A split account
  is a support question, not a security incident.
- **Harder:** a user who signs up with a password and later wants Google has to
  keep using the password. The refusal message must therefore name the real
  cause and route them back to password sign-in, or it reads as a bug.
- **We now live with:** `users.email` is `unique=True`
  (`back-end/src/ai_chat/auth/models.py:13`) and that is **load-bearing**. It
  aligns with this policy rather than being an independent constraint.
  Relaxing it — for instance to permit duplicate accounts — does not work
  around this ADR, it reopens this decision.

## Alternatives considered

- **Auto-link on a shared email** — rejected. Google treats account linking as a
  separate, deliberate flow with its own control, not as a side effect of
  "Sign in with Google"; building the silent version diverges from the
  provider's own model.
- **Auto-link Google, require the password for GitHub** — rejected, and recorded
  explicitly because it is defensible and a reader will assume it was chosen by
  accident. It gives the common case fewer steps, but the resulting rule varies
  by provider, is invisible at the UI, and has to be documented. More
  importantly, automatic linking is only safe when the provider asserts the
  address is verified. SuperTokens does surface `is_verified`
  (`thirdparty/interfaces.py:101`), but GitHub does not distinguish it reliably.
  A uniform rule avoids a per-provider exception that the user cannot see and
  that is easy to get wrong. An unverified shared address is an
  account-takeover vector.
- **Merge only when both providers have verified the address** — rejected as a
  special case of the above. It reintroduces the per-provider rule while adding
  a condition users cannot reason about.
- **Split accounts are cheap now and expensive later** — not an alternative, but
  the reason for not deferring. Creating them is trivial; reconciling them once
  users have conversations and quota history attached is not.

## Notes

This decision is currently a *default* rather than enforced code: nothing passes
the linking flag, so nothing links. That is a fragile kind of safety — the next
person to read `shouldTryLinkingWithSessionUser` sitting unset in
`SocialButtons.vue` will reasonably conclude it was an oversight. This ADR is
what makes it intentional.

If a future feature genuinely needs linking — an admin merge tool, a support
workflow — that is a deliberate addition with its own verification and its own
decision, not a relaxation of this rule.