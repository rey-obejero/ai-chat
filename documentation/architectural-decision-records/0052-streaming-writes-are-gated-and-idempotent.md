# ADR-0052: Streaming writes are gated, idempotent, and cancelled on disconnect

- **Status:** Accepted
- **Date:** 2026-10-17
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Every route that streams a reply takes a per-conversation generation lock (409
`CONVERSATION_BUSY`), every non-idempotent write carries a client-generated key
enforced by a unique constraint, and a client disconnect cancels the provider
stream and persists the partial reply.

## Context

Edit, regenerate, and send all mutate a conversation and then stream for
seconds. Three problems follow, and none is hypothetical at chat scale:

1. Two tabs (or a retry racing a first attempt) can mutate the same conversation
   concurrently; edit/regenerate delete rows as they go, so an interleaved write
   produces a non-deterministic transcript and two replies streaming into one
   conversation.
2. A dropped mobile connection re-sends a `POST`, duplicating a message; a
   double-clicked save can create two conversations that both claim the same
   staged attachments.
3. The stop button ended the *client's* SSE stream but not the provider call, so
   the server kept spending tokens, and the partial reply could be lost — which
   contradicts FR-8's "what was produced is kept".

## Decision

- **Generation gate.** `conversations.generating_at` is a timestamp checked and
  set atomically in a single conditional `UPDATE`. A write that finds it set and
  unexpired gets 409 `CONVERSATION_BUSY`; an expired stamp (older than
  `stream_grace_seconds`, default 120) is treated as free, so a crashed stream
  self-heals instead of wedging the conversation. A `finally` clears it on every
  exit path, including cancellation.
- **Idempotency.** Every logical write carries a client-generated `client_id`.
  A unique constraint on `(conversation_id, role, client_id)` makes a retry a
  structural no-op; a duplicate is answered with the already-stored reply rather
  than a second write. The constraint is scoped by role because a single key
  names one turn. Send mints a key per user turn; an edit and a regenerate each
  mint a fresh key for the reply they produce, so a later write against the same
  turn is its own attempt rather than a replay of the first — the retry that must
  replay carries the same key. An edit names the turn it replaces in
  `target_client_id`, because one key can no longer serve as both the attempt's
  identity and the target's. Every lookup is role-scoped, so the looser
  constraint does not weaken the guarantee.
- **Client-owned turn identity.** A locally-sent turn is addressed by the
  `client_id` it was created with, because the SDK assigns its own non-uuid id
  to the message it appends. The edit route resolves its target by server uuid
  first and by `client_id` (role-scoped) second, and `MessageRead` exposes
  `client_id` so a turn restored from history stays addressable by the same key.
- **Disconnect.** The SSE loop polls `request.is_disconnected()` alongside
  provider chunks; on a disconnect it closes the provider stream, keeps the
  accumulated text as the reply (stopped semantics), records the usage already
  spent, and clears the gate.
- **A delete racing a stream.** A delete is deliberately not gated, so the
  conversation can be gone before a reply completes. The reply and the activity
  stamp are then dropped — there is nothing left for them to belong to — while
  the reply's spend is still recorded, against no conversation: the tokens were
  paid for whatever became of the conversation they were spent in, and the ledger
  is the record of that.

## Consequences

- **Easier:** one writer per conversation; retries are safe; the stop button and
  a closed tab both stop the spend and keep the partial.
- **Harder:** the gate is one more state to reason about on every streaming
  route, and the disconnect path must be shielded from cancellation so its
  cleanup actually runs.
- **We now live with:** a 120-second grace window in which a genuinely hung
  worker blocks its conversation; and a client responsibility to keep its
  `client_id` stable across retries.

## Alternatives considered

- **Redis lease (SET NX + TTL)** — the standard answer once the app runs
  multiple instances; a DB row suffices for one, and is the recorded upgrade
  path (root `AGENTS.md`, Upgrade triggers).
- **Postgres advisory locks** — correct primitive, but holding a pool connection
  for a whole SSE stream shrinks the pool to the concurrent-stream count.
- **No gate (or ban-edit-while-streaming)** — does not defend a second tab.
- **Stripe-style `Idempotency-Key` header with a replay cache** — fully general,
  but its storage is infrastructure that a single Postgres does not need; also
  the recorded upgrade path.
- **Persist partials on a heartbeat instead of on disconnect** — more writes per
  stream to harden a different, rarer failure (whole-server crash).
