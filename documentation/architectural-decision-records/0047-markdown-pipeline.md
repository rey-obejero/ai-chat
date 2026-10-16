# ADR-0047: Markdown is parsed with escaped HTML, sanitised, and highlighted synchronously

- **Status:** Accepted
- **Date:** 2026-10-17
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Assistant replies are rendered with markdown-it (raw HTML escaped), sanitised by
DOMPurify as a second layer, and syntax-highlighted synchronously by
highlight.js over a curated language set — never by executing parsed markup.

## Context

ADR-0044 requires assistant Markdown and user plain text. That needs a parsing
pipeline that is safe on untrusted, arbitrary, and *partially streamed* content,
and that renders cheaply enough to re-run on every streamed chunk. Rendering
arbitrary HTML is the classic injection surface; highlighting an entire language
set would bloat the bundle.

## Decision

- **Stack:** markdown-it for parsing, DOMPurify for sanitising, highlight.js for
  colour. Parser options: `html: false` (raw HTML renders as visible text),
  `linkify: true`, `breaks: true`; tables on via the default preset.
- **Two independent layers:** the parser escapes raw HTML by default and refuses
  unsafe link protocols; DOMPurify runs afterwards on the generated HTML. The
  sanitizer must keep the generated `<button>`, `data-*` hooks, and
  `target`/`rel` on links.
- **Curated languages:** highlight.js core plus ten languages (js, ts, python,
  json, bash, xml, css, sql, yaml, markdown) with alias resolution. Measured
  ~73 KB gzip for the whole pipeline.
- **Synchronous, full re-render per update:** the accumulated text is parsed on
  each change; Vue's `computed` memoises per message, so only the streaming
  message re-parses. Measured ~0.6 ms per message, well inside the 15 ms chunk
  cadence.
- **Open-fence rule:** the trailing, still-streaming fence renders as a plain
  code block without highlighting, so the growing tail is never re-highlighted
  and the block never breaks mid-stream.
- **User text never goes through the pipeline:** it is interpolated (escaped by
  Vue), with fenced segments split out into plain monospace blocks.
- **Theme:** highlight.js `github` light only. The dark variant waits for WI-15.

## Consequences

- **Easier:** formatted replies with a small, auditable safety story; a bundle
  delta the front-end can carry.
- **Harder:** two rendering paths to keep consistent (ADR-0044); the sanitizer
  allowlist must track any new generated markup.
- **We now live with:** no light/dark highlight pair until WI-15, and no
  incremental parser state — which is what keeps the open-fence rule simple.

## Alternatives considered

- **marked** — comparable speed, but markdown-it's escaped-HTML default and
  built-in link validation leave less to configure safely.
- **Highlight in a Web Worker** — unnecessary at the measured cost, and it
  complicates the flush-per-chunk render.
- **A full highlight.js bundle** — pays for dozens of unshipped languages.
- **Trust the parser alone (no sanitizer)** — removes the second independent
  layer the safety story depends on.
