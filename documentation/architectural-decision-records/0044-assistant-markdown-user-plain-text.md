# ADR-0044: Assistant messages render as Markdown, user messages as plain text

- **Status:** Accepted
- **Date:** 2026-10-06
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

The assistant's replies are rendered as formatted Markdown; the user's own
messages are shown as plain text with line breaks preserved.

## Context

Replies routinely contain formatting and code, which is far more readable when
rendered. User input, by contrast, is untrusted and arbitrary: rendering it as
rich markup invites injection and produces surprising transformations ("why did
my asterisks disappear?"). The two directions do not need the same treatment.

## Decision

Assistant messages render as Markdown — headings, lists, tables, links,
blockquotes, and syntax-highlighted, copyable code — and never execute code or
scripts. User messages are displayed as literal text with line breaks preserved
and long code shown in a scrollable monospace block; user content is never
interpreted as markup.

## Consequences

- **Easier:** readable replies without an injection surface from user input.
- **Harder:** two rendering paths and a Markdown pipeline that must be safe for
  streamed, partial content.
- **We now live with:** an asymmetric interface that must be applied
  consistently.

## Alternatives considered

- **Render both** — consistent, but unsafe and confusing for user input.
- **Render neither** — safest, but replies lose all formatting.
