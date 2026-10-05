# Functional Requirements — AI Chat

| | |
|---|---|
| **Owner** | rey-obejero |
| **Status** | Draft |
| **Version** | 1.1 |
| **Date** | 2026-10-06 |
| **References** | the ADRs and `DESIGN.md` under `documentation/`; the issue tracker |

## 1. Introduction

### 1.1 Purpose
This document specifies the functional and non-functional requirements of the AI
Chat assistant: a multi-user chat assistant with persistent conversations,
document retrieval, tools, and custom skills. It is the source of truth for
*what* the product must do. Each requirement is testable and traces to a work
item in the issue tracker.

### 1.2 Scope
It covers the product's user-facing capabilities: access and identity,
conversations, composition and input, assistant behaviour, rendering, document
retrieval, tools, appearance and language, sharing, and settings.

Out of scope: production deployment (§5). Sequencing, priority, and milestones
are not specified here; they live in the issue tracker.

### 1.3 Intended audience
Implementers and reviewers. A reader should be able to build, test, and review
each requirement without further interpretation.

### 1.4 Conventions
- **FR-n** — a functional requirement. **NFR-n** — a non-functional requirement.
- **WI-n** — a work item: the unit of work filed as an issue (Appendix A).
- **Statement** uses "shall". **Acceptance criteria** are testable.
- **Source** names the work item that implements the requirement.
- **Verification** is one of `test`, `demo`, or `inspection`.
- **Guest** — an unauthenticated user with their own isolated conversations.
- **Temporary conversation** — a conversation kept out of history unless saved.
- **BYOK** — bring your own key: the user supplies a third-party model provider.

## 2. Users

- **Evaluator** — no account; wants to try a real conversation first.
- **Returning user** — signed in; wants history and preferences to persist.
- **Power user** — brings a key, attaches documents, uses tools and skills.
- **Privacy-minded user** — wants incognito conversations and clear retention.

## 3. Functional requirements

### 3.1 Access & identity

#### FR-1 Email/password sign-up and sign-in
- **Statement** — A user shall create an account and sign in with an email
  address and a password, and shall sign out.
- **Rationale** — Accounts make conversations and settings personal and durable.
- **Acceptance criteria**
  - A valid email and password create an account and sign the user in.
  - One email address maps to exactly one account.
  - A signed-in session persists until it expires or the user signs out.
  - Signing out ends access on that device.
- **Source** — WI-2 · **Verification** — test

#### FR-2 Password policy
- **Statement** — The system shall reject a password that is shorter than 8
  characters, that is a weak or common pattern, or that appears in breached-
  password data.
- **Rationale** — Weak or breached passwords are the most common account-takeover
  vector.
- **Acceptance criteria**
  - A password under 8 characters is rejected.
  - A password judged weak by the strength check is rejected.
  - A password present in the breached-password service is rejected.
  - Rejection occurs before the account is created, with a clear reason.
- **Source** — WI-3 · **Verification** — test

#### FR-3 Password reset
- **Statement** — A user shall request a reset link by email and set a new
  password from it, and all existing sessions shall end when the password changes.
- **Rationale** — Users lose passwords; a reset must not become a takeover path.
- **Acceptance criteria**
  - A reset link is emailed to a registered address.
  - The request reveals nothing about whether an address has an account.
  - Following a valid, unexpired link sets a new password under FR-2.
  - A completed reset ends all existing sessions.
- **Source** — WI-3 · **Verification** — test

#### FR-4 Email verification
- **Statement** — The system shall send a verification email, and shall apply a
  lower usage allowance to an unverified account until the address is verified.
- **Rationale** — Verification discourages throwaway accounts without blocking
  first use.
- **Acceptance criteria**
  - A verification email is sent shortly after sign-up.
  - An unverified account has half the normal chat allowance and no uploads.
  - A nudge is shown when the reduced allowance is reached.
  - Verification never blocks basic sign-in or reading.
- **Source** — WI-3 · **Verification** — test

#### FR-5 Social sign-in
- **Statement** — A user shall sign in with a configured social provider as an
  alternative to a password.
- **Rationale** — Lower sign-in friction for users who prefer not to hold a
  password here.
- **Acceptance criteria**
  - Only providers configured for the deployment are offered.
  - The same provider identity always maps to the same account.
  - A provider sign-in whose email already has an account is refused, and the
    user is directed to their existing method.
  - The application never receives the provider password.
- **Source** — WI-2 · **Verification** — test

#### FR-6 Guest use
- **Statement** — An unauthenticated visitor shall chat without an account, and
  shall claim their conversations by signing up.
- **Rationale** — Removes the sign-up wall in front of the product's first
  impression.
- **Acceptance criteria**
  - A visitor with no account can start and continue a conversation.
  - A guest sees only their own conversations.
  - Guest usage is rate-limited and spend-capped.
  - Signing up moves the guest's conversations into the new account, orphaning
    none.
  - Guest conversations are deleted within 30 days.
- **Source** — WI-1 · **Verification** — test

#### FR-7 Display-name onboarding
- **Statement** — On first sign-in the system shall ask the user how they wish to
  be addressed, defaulting to the local part of their email address verbatim, and
  the name shall be editable later.
- **Rationale** — A name makes the product personal without a form barrier.
- **Acceptance criteria**
  - The prompt appears once, and can be skipped.
  - The default is the email local part, unchanged (e.g. `s82jdna`).
  - The name is 1–50 characters and is filtered for profanity.
  - The name is never blank and is editable from settings.
- **Source** — WI-4 · **Verification** — demo

### 3.2 Conversations & chat

#### FR-8 Streaming replies
- **Statement** — The system shall display the assistant's reply progressively as
  it is produced, and shall let the user stop generation.
- **Rationale** — Perceived speed is central to a chat product.
- **Acceptance criteria**
  - Reply text appears incrementally before completion.
  - The user can stop an in-flight reply; what was produced is kept.
  - A reply always ends with a completed, stopped, or failed state.
- **Source** — WI-5 · **Verification** — test

#### FR-9 Conversation context
- **Statement** — The assistant shall use the earlier turns of the current
  conversation as context.
- **Rationale** — Follow-up questions only work with memory of prior turns.
- **Acceptance criteria**
  - A follow-up referring to an earlier turn is answered consistently with it.
  - Only the current conversation and the user's own data inform a reply.
  - A reply never uses another user's content.
- **Source** — WI-5 · **Verification** — test

#### FR-10 Message persistence
- **Statement** — The system shall store both the user's and the assistant's
  messages in the order they occurred.
- **Rationale** — Conversations must survive reload and be resumable.
- **Acceptance criteria**
  - Each message is stored exactly once, in order.
  - Reopening a conversation shows the same messages in the same order.
  - A dropped connection or refresh does not lose received content or corrupt the
    conversation.
- **Source** — WI-5 · **Verification** — test

#### FR-11 Conversation list and resume
- **Statement** — The system shall list the user's conversations and let them
  reopen and continue one.
- **Rationale** — Past conversations are the product's memory.
- **Acceptance criteria**
  - The list shows only the user's own conversations, most recent activity first.
  - Each conversation has an auto-generated title derived from its first user
    message; the title is inline-editable.
  - Opening a conversation restores its full history and allows continuation.
- **Source** — WI-7 · **Verification** — test

#### FR-12 Temporary conversation
- **Statement** — A signed-in user shall start a temporary conversation that is
  excluded from history unless they save it.
- **Rationale** — Some conversations should not persist by default.
- **Acceptance criteria**
  - A temporary conversation does not appear in the list.
  - It is not stored on the server until saved.
  - Saving converts it into an ordinary conversation, including its attachments.
  - Unsaved, it cannot be reopened after the user leaves it.
  - Personalization is chosen before it starts and cannot change mid-conversation.
- **Source** — WI-8 · **Verification** — test

#### FR-13 Edit, regenerate, and stop
- **Statement** — The user shall edit a message, regenerate an assistant reply,
  and stop generation.
- **Rationale** — Users need to steer a conversation that went the wrong way.
- **Acceptance criteria**
  - Editing or regenerating replaces the affected turn and everything after it,
    leaving no duplicates.
  - Stopping keeps what was already produced.
- **Source** — WI-6 · **Verification** — test

#### FR-14 Copy and quote
- **Statement** — The user shall copy a message and quote a message into the
  composer.
- **Rationale** — Users reuse and reference content.
- **Acceptance criteria**
  - Copying places the exact message text on the clipboard.
  - Quoting inserts the exact referenced text, attributed to its author.
  - No operation exposes content across users.
- **Source** — WI-6 · **Verification** — demo

#### FR-15 Search conversations
- **Statement** — The user shall search their conversations by content.
- **Rationale** — A long history is useless without search.
- **Acceptance criteria**
  - Results include only the searcher's own conversations.
  - The search term is not stored or shared.
- **Source** — WI-7 · **Verification** — test

#### FR-16 New, rename, delete
- **Statement** — The user shall create, rename, and delete a conversation.
- **Rationale** — Basic lifecycle management.
- **Acceptance criteria**
  - Creating starts an empty conversation.
  - Renaming changes the title and never alters history.
  - Deleting removes the conversation permanently and everywhere.
- **Source** — WI-7 · **Verification** — test

#### FR-17 Pin, favourite, archive
- **Statement** — The user shall pin, favourite, or archive a conversation.
- **Rationale** — Keeps an active list manageable without deleting.
- **Acceptance criteria**
  - Each state changes only how the list is presented.
  - None of them alters a conversation's content or ownership.
- **Source** — WI-7 · **Verification** — demo

### 3.3 Composer & input

#### FR-18 File attachments
- **Statement** — The user shall attach files to a conversation for the assistant
  to read, subject to per-message, per-conversation, per-user, and time-based
  limits.
- **Rationale** — Users bring material into the conversation.
- **Acceptance criteria**
  - TXT, MD, PDF, and DOCX files can be attached and are available across the
    conversation.
  - Limits are 3 per message, 10 per conversation, and 50 stored per user, plus
    20 per day, 100 per week, and 300 per month.
  - Each attachment shows uploading, ready, or failed.
  - No file is processed or served until it has been verified safe.
  - A failed upload leaves nothing behind; a file is never lost before the reply
    that uses it.
  - Limits and quotas reset on schedule and are enforced before completion.
- **Source** — WI-9 · **Verification** — test

#### FR-19 Image input and camera
- **Statement** — The user shall send images, and capture them with a camera
  where the device provides one.
- **Rationale** — Visual input is a common chat need.
- **Acceptance criteria**
  - An image can be attached and reaches the assistant.
  - A failed capture or upload stores nothing.
  - An image is visible only to its sender.
- **Source** — WI-9 · **Verification** — demo

#### FR-20 Voice dictation
- **Statement** — The user shall dictate a message by speaking, and edit the
  resulting text before sending.
- **Rationale** — Faster input on mobile and hands-busy contexts.
- **Acceptance criteria**
  - Speech is transcribed into the composer.
  - The transcribable content is only the speaker's own speech.
  - The text is editable before sending.
  - Audio is not retained after transcription unless the user is told otherwise.
- **Source** — WI-9 · **Verification** — demo

#### FR-21 Slash-command palette
- **Statement** — Typing `/` shall open a list of available commands and skills;
  selecting one shall invoke it.
- **Rationale** — Discoverable access to skills without a menu.
- **Acceptance criteria**
  - Typing `/` opens the palette and never sends a message.
  - Only a deliberate selection runs a command.
- **Source** — WI-10 · **Verification** — demo

#### FR-22 Suggested prompts
- **Statement** — An empty conversation shall offer starter prompts.
- **Rationale** — Reduces the blank-page problem for new users.
- **Acceptance criteria**
  - Suggestions are shown for an empty conversation.
  - Nothing is sent or run until the user acts.
- **Source** — WI-10 · **Verification** — demo

### 3.4 Assistant behaviour & personalisation

#### FR-23 Model picker
- **Statement** — The user shall choose which model answers a conversation.
- **Rationale** — Different tasks suit different models.
- **Acceptance criteria**
  - The choice applies to the whole conversation.
  - The system never switches models silently; any switch is disclosed.
- **Source** — WI-11 · **Verification** — demo

#### FR-24 Custom instructions
- **Statement** — The user shall set persistent instructions that shape the
  assistant's replies for their account.
- **Rationale** — Repeated preferences should not be restated every time.
- **Acceptance criteria**
  - Instructions apply to every reply for the account.
  - Changing them never rewrites past messages.
  - A temporary conversation can opt out.
- **Source** — WI-11 · **Verification** — test

#### FR-25 Response style and tone
- **Statement** — The user shall choose a response style (for example, length or
  formality) that applies to their replies.
- **Rationale** — Output should fit the user's context.
- **Acceptance criteria**
  - The chosen style applies consistently to the account's replies.
  - Changing it never rewrites past messages.
- **Source** — WI-11 · **Verification** — demo

#### FR-26 Thinking indicator
- **Statement** — The system shall indicate when the model is still working.
- **Rationale** — Silence is indistinguishable from a hang.
- **Acceptance criteria**
  - A working state is shown between send and the first token, and while tools
    run.
  - The indicator never shows completion while work continues, nor persists after
    the reply ends.
- **Source** — WI-11 · **Verification** — demo

### 3.5 Rendering & output

#### FR-27 Markdown rendering and code highlighting
- **Statement** — The system shall render assistant replies as formatted Markdown
  with syntax-highlighted, copyable code, and shall display user messages as
  plain text.
- **Rationale** — Formatted output is far more readable; user text must never be
  interpreted as markup.
- **Acceptance criteria**
  - Assistant Markdown renders headings, lists, tables, links, blockquotes, and
    code blocks.
  - Code is highlighted for a common set of languages and has a copy control.
  - Very long code blocks scroll and can be expanded.
  - A partially streamed reply renders without breaking or dropping text.
  - Malformed markup degrades to readable text.
  - User messages show their literal text with line breaks preserved.
  - Rendered content never executes code or scripts.
- **Source** — WI-12 · **Verification** — test

### 3.6 Knowledge & retrieval

#### FR-28 Document upload
- **Statement** — The user shall upload documents to be indexed for retrieval.
- **Rationale** — The product's answer quality depends on the user's own material.
- **Acceptance criteria**
  - TXT, MD, PDF, and DOCX documents can be uploaded.
  - Documents are private to the uploader.
  - No document is processed until it has been verified safe.
  - A failed upload leaves nothing behind.
- **Source** — WI-13 · **Verification** — test

#### FR-29 Document Q&A with citations
- **Statement** — When an answer draws on the user's documents, the system shall
  cite the source document(s).
- **Rationale** — Users must be able to verify an answer.
- **Acceptance criteria**
  - Every citation names a real source.
  - A citation only ever references a document the asker may access.
- **Source** — WI-13 · **Verification** — test

#### FR-30 Hybrid search
- **Statement** — Retrieval shall combine keyword and semantic matching.
- **Rationale** — Neither alone retrieves well across varied material.
- **Acceptance criteria**
  - Retrieval returns documents the asker may access, and only those.
  - Both keyword and semantic matches can surface a relevant document.
- **Source** — WI-13 · **Verification** — test

#### FR-31 Document management
- **Statement** — The user shall see each document's ingest status and delete or
  re-index a document.
- **Rationale** — Uploaded material must be manageable.
- **Acceptance criteria**
  - Statuses reflect reality (processing, ready, failed).
  - Deleting a document removes it from future answers.
- **Source** — WI-13 · **Verification** — test

### 3.7 Agents & automation

#### FR-32 Tool calling
- **Statement** — The assistant shall call a tool mid-answer when the task
  requires it, and feed the result back into its reply.
- **Rationale** — Some questions need live data or computation.
- **Acceptance criteria**
  - A tool runs only with the user's permission and only on the user's data.
  - The result is reflected in the reply.
  - A failed tool degrades gracefully and never corrupts the reply.
- **Source** — WI-14 · **Verification** — test

#### FR-33 Skill invocation
- **Statement** — The user shall invoke a named skill, which applies its
  instructions to the conversation.
- **Rationale** — Reusable, user-facing capabilities without new code per use.
- **Acceptance criteria**
  - A skill runs only when chosen by the user or clearly disclosed.
  - A skill's instructions never override safety or privacy rules.
- **Source** — WI-14 · **Verification** — test

#### FR-34 Web search
- **Statement** — The assistant shall search the live web and use the results in
  an answer.
- **Rationale** — Some questions depend on current information.
- **Acceptance criteria**
  - Cited web sources are real and reachable.
  - The assistant never presents an invented link as a search result.
- **Source** — WI-14 · **Verification** — test

#### FR-35 Document generation
- **Statement** — The assistant shall produce a complete document and save it for
  the user.
- **Rationale** — Some requests are for a deliverable, not a chat answer.
- **Acceptance criteria**
  - The generated document belongs to the requesting user.
  - It is never overwritten by, or exposed to, another user.
- **Source** — WI-14 · **Verification** — test

### 3.8 Appearance & language

#### FR-36 Dark mode
- **Statement** — The user shall choose a light theme, a dark theme, or to follow
  the system; the choice shall follow their account across devices.
- **Rationale** — Comfort and accessibility in different environments.
- **Acceptance criteria**
  - Both themes meet the contrast requirement (NFR-5).
  - The choice is applied from the account on any device.
  - The wrong theme is never shown while the interface loads.
  - Switching themes loses no work (drafts, scroll, open dialogs).
- **Source** — WI-15 · **Verification** — test

#### FR-37 Internationalization
- **Statement** — The user shall use the interface in their chosen language, at
  launch English or Chinese (Simplified).
- **Rationale** — The product should not require English.
- **Acceptance criteria**
  - Every user-facing string comes from a translation.
  - A missing translation falls back to English, never to a blank or a raw key.
  - The chosen language is remembered.
  - Switching language loses no unsaved work.
  - The chosen script (Simplified or Traditional) is honored.
- **Source** — WI-15 · **Verification** — test

### 3.9 Sharing & collaboration

#### FR-38 Public share link
- **Statement** — The user shall create a read-only public link to a conversation
  and revoke it.
- **Rationale** — Sharing an answer is a common need.
- **Acceptance criteria**
  - Anyone with the link can view, and only view.
  - The shared view never exposes content beyond that conversation.
  - Revoking the link ends access.
- **Source** — WI-16 · **Verification** — test

### 3.10 Settings & account

#### FR-39 User settings
- **Statement** — The user shall manage their preferences in one settings
  surface: profile, appearance, usage and quotas, model provider, custom
  instructions, language, and account and security.
- **Rationale** — One place to manage an account.
- **Acceptance criteria**
  - The listed sections are present.
  - A change affects only the signed-in account and survives a reload.
  - Sensitive values (keys, passwords) are never shown back in full.
  - Leaving mid-edit never leaves a half-saved setting.
- **Source** — WI-17 · **Verification** — demo

#### FR-40 AI provider (Auto / BYOK)
- **Statement** — The user shall use the server-provided model, or connect their
  own compatible third-party provider with a base URL, key, and model.
- **Rationale** — Power users may prefer their own provider and billing.
- **Acceptance criteria**
  - Auto works with no key.
  - A BYOK key is used only for its owner's requests and is never shown back in
    full or logged.
  - Switching provider never exposes another user's key.
  - BYOK usage is not counted against the server's token quota but is still
    rate-limited.
- **Source** — WI-17 · **Verification** — test

#### FR-41 Usage and quota display
- **Statement** — The user shall see their remaining allowance.
- **Rationale** — Limits should never be a surprise.
- **Acceptance criteria**
  - The figure reflects real usage and is visible only to its owner.
  - Reaching a limit is communicated before the request is blocked.
- **Source** — WI-17 · **Verification** — test

## 4. Non-functional requirements

- **NFR-1 Security — isolation.** A user, including a guest, shall be able to
  access only their own data. *Verification: test.*
- **NFR-2 Security — credentials.** A session credential shall never be readable
  by client script or stored in web storage. *Verification: inspection.*
- **NFR-3 Content safety.** Uploaded content shall not be processed or served
  until it has been verified safe. *Verification: test.*
- **NFR-4 Performance.** The p95 time to first token shall be at most 2 seconds
  on the reference development host, and a conversation list of 200 items shall
  render within 1 second. *Verification: test.*
- **NFR-5 Accessibility.** Both themes shall meet WCAG AA contrast, and every
  primary flow shall be operable by keyboard alone. *Verification: inspection.*
- **NFR-6 Reliability.** No message turn shall be half-persisted, and a
  mid-stream failure shall surface as an error rather than silence.
  *Verification: test.*
- **NFR-7 Privacy — retention.** Guest data shall be deleted within 30 days, and
  a temporary conversation shall not be stored until saved.
  *Verification: inspection.*
- **NFR-8 Observability.** Logs shall be structured and shall contain no secrets
  or message content. *Verification: inspection.*

## 5. Out of scope

Only **production deployment** — a purchased domain, a production host, and TLS
— is out of scope. Sequencing, priority, and future (unbuilt) capabilities are
not specified here; they live in the issue tracker.

## 6. Open questions

- The model by which a guest is identified (deferred to an ADR).
- The token figure behind the unverified "half" cap (FR-4).
- Whether attachments carry a byte-size cap in addition to file counts (FR-18).
- Whether the profanity filter is locale-aware for Chinese names (FR-7).
- When the hidden summarization of long conversations triggers (FR-9/FR-10).

## Appendix A — Work items

Each work item is filed as a GitHub issue; record its number in the last column
once filed. A requirement's **Source** names its work item.

| WI | Work item | Requirements | Issue |
|---|---|---|---|
| WI-1 | guest-access | FR-6 | — |
| WI-2 | account-sign-in | FR-1, FR-5 | — |
| WI-3 | password-and-recovery | FR-2, FR-3, FR-4 | — |
| WI-4 | display-name | FR-7 | — |
| WI-5 | chat-streaming | FR-8, FR-9, FR-10 | — |
| WI-6 | message-actions | FR-13, FR-14 | — |
| WI-7 | conversation-history | FR-11, FR-15, FR-16, FR-17 | — |
| WI-8 | temporary-conversations | FR-12 | — |
| WI-9 | attachments-and-input | FR-18, FR-19, FR-20 | — |
| WI-10 | commands-and-prompts | FR-21, FR-22 | — |
| WI-11 | assistant-personalisation | FR-23, FR-24, FR-25, FR-26 | — |
| WI-12 | markdown-rendering | FR-27 | — |
| WI-13 | documents-and-retrieval | FR-28, FR-29, FR-30, FR-31 | — |
| WI-14 | tools-and-skills | FR-32, FR-33, FR-34, FR-35 | — |
| WI-15 | appearance-and-language | FR-36, FR-37 | — |
| WI-16 | sharing | FR-38 | — |
| WI-17 | settings-and-providers | FR-39, FR-40, FR-41 | — |

Work item IDs are provisional; they are replaced by the issue number once filed.
User stories are not kept in this document — they live in the issue tracker and
inform each work item's scope.
