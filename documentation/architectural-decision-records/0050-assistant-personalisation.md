# ADR-0050: Personalisation is account settings plus a per-conversation model choice

- **Status:** Accepted
- **Date:** 2026-10-17
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Instructions and a response style live on the account and compose into one system
message the provider receives first; the model is a per-conversation choice from a
list the deployment configures, and every change to it is disclosed in the
transcript as a system-role caption.

## Context

FR-23, FR-24 and FR-25 ask for a model picker, standing instructions that shape
replies, and a response style. Three forces shape how:

1. Nothing may rewrite what was already said. Instructions, style and model all
   have to apply from the next reply onward, which makes them settings rather than
   transcript edits.
2. The provider boundary already takes `model: str | None` (ADR-0018), and history
   is composed per request from stored rows (ADR-0022), so both settings can be
   applied at request time with no new provider work.
3. What a deployment can serve is configuration, not code: which models are
   reachable depends on the key, the base URL, and what the operator will pay for.
   A list baked into the API or the SPA is wrong in some environment at all times.

Silence is the risk that decides the shape. A reply that quietly came from a
different model than the user chose, and instructions that quietly changed the
assistant's behaviour, are both invisible in the transcript.

## Decision

- **Instructions and style are account columns.** `users.instructions` (text,
  nullable, 2000-character cap enforced at `PUT /preferences`) and
  `users.response_style` (`varchar(16)`, `NOT NULL`, default `default`, one of
  `default | concise | detailed | formal | casual`). `GET /me` and the save
  response both expose them, so the settings form loads and refreshes in one call.
- **One composer, one system message.** `llm/prompts.py` owns
  `build_system_prompt(instructions, style)`: instructions first, then the style's
  fixed sentence, nothing when the account asked for neither, and a 4000-character
  ceiling that truncates with a logged warning. The fragments are data keyed by the
  style enum, so the vocabulary and its wording cannot drift apart.
- **The served list is a setting.** `llm_models` (default `[llm_model]`, which is
  always in it) drives `GET /models` as `{id, label, is_default}`. Adding a model
  is an environment change, and `is_default` marks `llm_model`, so a request with
  no choice of its own always has somewhere to go.
- **The model is a conversation property.** `conversations.model` is nullable;
  `None` means the deployment default. `POST /conversations` and
  `PATCH /conversations/{id}` accept a model and check it against the list the
  deployment serves *then*. The effective model is resolved per request and handed
  to the unchanged provider port.
- **Every change is disclosed.** A switch writes a `system`-role caption ("Model
  set to X") into the transcript, which the interface renders as a centred caption.
  A stored choice the deployment no longer serves is replaced by the default,
  persisted, and captioned the same way, so the substitution is disclosed once and
  the retired id never reaches a provider.
- **Captions ride the history.** `build_history` sends them as system messages, and
  the account's prompt is prepended ahead of the transcript, which keeps it the
  first system message.

## Consequences

- **Easier:** another served model or a new style is configuration and data, not
  code; one function decides what the provider is told; the model a reply used is
  legible from the transcript alone, after the fact.
- **Harder:** what a model was told is now assembled from a column, a data table
  and a caption, so answering that question means reading three places. The ceiling
  truncates silently to the caller (it is logged), and today's inputs cannot reach
  it — it guards future ones.
- **We now live with:** the capability caveat that an OpenAI-compatible adapter
  need not honour more than one system message, or one placed after a user turn. An
  adapter that keeps only the first still gets the instructions, because they lead;
  one that drops later system messages does not see a caption, which the transcript
  still shows. A model removed from `llm_models` is not restored by adding it back:
  fallback has already replaced the stored choice. And because a caption is a
  message, rewriting an earlier turn discards the captions after it (ADR-0052's
  rewind), so a switch recorded there leaves the transcript: the picker still
  reports the model in force, and saving that same model again writes nothing, so
  only a further change is captioned.

## Alternatives considered

- **Style as provider parameters (temperature, `top_p`)** — a style is an
  instruction the user can read and repeat, not an opaque sampling knob that means
  something different at every vendor.
- **Instructions prepended to the latest user turn** — invisible in the transcript
  afterwards, and it makes the user's own words ambiguous with the account's.
- **Instructions per conversation** — FR-24's opt-out belongs to temporary
  conversations (WI-8), which pass options at start; until then the account is the
  only source, and a conversation-level override would need a second form.
- **The picker's list stored in the database** — a deploy-time concern dressed up
  as data; an environment variable plus a settings-driven list is one fewer moving
  part.
- **Rejecting a request whose stored model is gone** — turns an operator's
  configuration change into a conversation the user cannot repair from the composer.
- **Disclosing a switch through an SSE part or a response header** — the wire
  format is the AI SDK's (ADR-0012), and a disclosure that vanishes on reload is
  not a record.
