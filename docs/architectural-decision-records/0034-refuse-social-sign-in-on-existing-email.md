# ADR-0034: A social sign-in is refused when its email already has an account

- **Status:** Accepted
- **Date:** 2026-10-04
- **Deciders:** Rey Obejero
- **Supersedes:** ADR-0028
- **Superseded by:** —

## TL;DR

A social sign-in presenting an email that already belongs to another account is
refused, and the refusal is **enforced in code** — the SuperTokens default does
the opposite and would create a second account for that email.

## Context

ADR-0028 decided the policy — identities are never merged and a duplicate is
never created — but it described the SDK as already enforcing it. It does not.

Verified against the installed SDK and observed end to end:

- `AccountLinkingRecipe.is_sign_in_allowed` returns `True` for a primary user
  (`accountlinking/recipe.py:300-305`), and the default sign-up check lets a
  verified provider email through. The result is a **second** primary user with
  the same email, not a refusal.
- `shouldTryLinkingWithSessionUser` does not change this: it governs linking to
  the *current session* user, which is a different question. Leaving it unset,
  as ADR-0028 relied on, enforces nothing.
- The second account then collides with `users.email`'s unique constraint: the
  original user's next `/me` returns 500. Observed in the e2e suite — the social
  session user id differed from the seeded user's, and the seeded user then
  failed with `INTERNAL_ERROR`.

So the front end's "that address already has an account" branch was unreachable,
and the failure mode was worse than no refusal: it was a duplicate account and a
server error.

## Decision

- Enforce the refusal in the third-party recipe's `sign_in_up`, the one function
  every provider funnels through. Before signing in, look up users by the
  provider email; if any exists and it is **not** this third-party identity,
  return `SignInUpNotAllowed`, which becomes the front end's existing-account
  message.
- A returning social identity is allowed: its own login method matches the
  third-party id, so there is no conflict.
- This is uniform across providers, as ADR-0028 intended.
- `get_or_create_user` handles the same-user insert race (two first requests
  both inserting) by re-reading the committed row instead of returning 500. A
  *different* user with the same email cannot reach it, because it is refused
  earlier.

## Consequences

- **Easier:** one rule, enforced where every provider passes; the existing
  account message is reachable; `users.email` uniqueness stops being a latent
  500.
- **Harder:** the refusal is application code wrapping a vendor function, so a
  vendor change to `sign_in_up` is a place to check. The lookup adds one core
  call per social sign-in.
- **We now live with:** a user who signed up with a password and later wants a
  social provider must keep using the password. The refusal message names the
  real cause and routes them back.

## Alternatives considered

- **Rely on the SDK default** — what ADR-0028 assumed, and what the evidence
  shows is not a refusal. Rejected.
- **Accept verified-email linking and let the provider email resolve to the
  existing account** — a defensible policy, but it is a different product
  decision and does not match the requirement that identities never merge.
  Rejected here.
- **Enforce by relaxing `users.email` uniqueness** — rejected; it removes the
  safety net without preventing the duplicate, and moves the failure later.
- **Refuse only unverified emails** — rejected; it varies by provider and is
  invisible to the user, which is the per-provider rule ADR-0028 already
  rejected.
