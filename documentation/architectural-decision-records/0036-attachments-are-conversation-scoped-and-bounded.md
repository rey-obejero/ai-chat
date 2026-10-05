# ADR-0036: Attachments are conversation-scoped, bounded, and screened

- **Status:** Accepted
- **Date:** 2026-10-06
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Files attach to a conversation, are limited per message, per conversation, per
user, and per day/week/month, and are malware-screened before any use.

## Context

Users bring their own material into a chat. Unbounded uploads are a storage and
cost risk and an abuse vector, and uploaded files can carry malware. The object
store for raw files (SeaweedFS) is planned but not yet in the stack.

## Decision

- **Scope:** an attachment belongs to the whole conversation, not a single
  message.
- **Limits:** 3 per message, 10 per conversation, 50 stored per user.
- **Time quotas:** 20 per day, 100 per week, 300 per month; reset on schedule.
- **Safety:** no file is processed or served until it has been screened and
  found safe; a failed upload leaves nothing behind.

## Consequences

- **Easier:** predictable storage growth; a single place to enforce abuse limits.
- **Harder:** per-user storage accounting; a screening step in the ingest path.
- **We now live with:** quota windows that must reset, and a file store that has
  to be decided separately.

## Alternatives considered

- **Message-scoped attachments** — simpler ownership, but files are lost from
  follow-up turns.
- **No time quotas** — smaller build, larger abuse surface.
- **Client-side storage** — no cost, but no shared access or screening.
