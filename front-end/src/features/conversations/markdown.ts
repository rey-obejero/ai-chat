import DOMPurify from 'dompurify'
import hljs from 'highlight.js/lib/core'
import bash from 'highlight.js/lib/languages/bash'
import css from 'highlight.js/lib/languages/css'
import javascript from 'highlight.js/lib/languages/javascript'
import json from 'highlight.js/lib/languages/json'
import markdown from 'highlight.js/lib/languages/markdown'
import python from 'highlight.js/lib/languages/python'
import sql from 'highlight.js/lib/languages/sql'
import typescript from 'highlight.js/lib/languages/typescript'
import xml from 'highlight.js/lib/languages/xml'
import yaml from 'highlight.js/lib/languages/yaml'
import MarkdownIt from 'markdown-it'
import 'highlight.js/styles/github.css'

// The curated language set (ADR-0047): core plus the ten languages the product
// highlights. highlight.js resolves common aliases (js, ts, py, sh, html) from
// these definitions.
const LANGUAGES: Record<string, Parameters<typeof hljs.registerLanguage>[1]> = {
  bash,
  css,
  javascript,
  json,
  markdown,
  python,
  sql,
  typescript,
  xml,
  yaml,
}

for (const [name, definition] of Object.entries(LANGUAGES)) {
  hljs.registerLanguage(name, definition)
}

/** Height cap beyond which a fence scrolls, and can be expanded (DESIGN.md). */
export const CODE_EXPAND_LINE_THRESHOLD = 20

const SVG_BODY =
  'viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"'

const COPY_ICON = `<svg class="md-code__icon" ${SVG_BODY}><path d="M9 9h10a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2V11a2 2 0 0 1 2-2Z"/></svg>`
const CHECK_ICON = `<svg class="md-code__check" ${SVG_BODY}><path d="M20 6 9 17l-5-5"/></svg>`

const md = new MarkdownIt({
  html: false, // raw HTML renders as visible text, never as markup
  linkify: true, // bare URLs become links
  breaks: true, // single newlines become line breaks (the chat convention)
})

declare module 'markdown-it' {
  interface Env {
    /** Fence ordinal within the current render — the block's stable DOM key. */
    blockOrdinal?: number
    /** Whether the source's final fence is still open (a mid-stream reply). */
    openFence?: boolean
  }
}

/**
 * True when the source ends with a fence that was never closed — the normal state
 * of a code block still streaming in.
 */
function lastFenceIsOpen(source: string): boolean {
  let open = false
  let marker = ''
  for (const line of source.split('\n')) {
    const match = line.match(/^\s*(`{3,}|~{3,})/)
    if (!match) continue
    if (!open) {
      open = true
      marker = match[1]![0]!
    } else if (match[1]![0] === marker) {
      open = false
      marker = ''
    }
  }
  return open
}

/** Highlight a closed fence; leave an open or unknown-language fence as plain text. */
function highlight(code: string, language: string, open: boolean): string {
  if (!open && language && hljs.getLanguage(language)) {
    try {
      return hljs.highlight(code, { language, ignoreIllegals: true }).value
    } catch {
      return md.utils.escapeHtml(code)
    }
  }
  return md.utils.escapeHtml(code)
}

// A code fence renders as a self-contained block: header (language label + copy
// control), the code body, and — past the line threshold — an expand footer. The
// component owns the interactive state and re-applies it after each re-render,
// so this markup only carries the hooks.
md.renderer.rules.fence = (tokens, idx, _options, env): string => {
  const ordinal = (env?.blockOrdinal ?? 0) + 1
  if (env) env.blockOrdinal = ordinal

  const token = tokens[idx]!
  const info = token.info ? token.info.trim() : ''
  const language = info.split(/\s+/)[0]!.toLowerCase()
  const label = language || 'code'
  const open = (env?.openFence ?? false) && idx === tokens.length - 1
  const lineCount = token.content.replace(/\n$/, '').split('\n').length

  const header =
    `<div class="md-code__header"><span class="md-code__lang">${md.utils.escapeHtml(label)}</span>` +
    `<button type="button" class="md-code__copy" data-copy aria-label="Copy code">${COPY_ICON}${CHECK_ICON}</button></div>`
  const body = `<pre class="md-code__body"><code class="hljs language-${md.utils.escapeHtml(label)}">${highlight(
    token.content,
    language,
    open,
  )}</code></pre>`
  const footer =
    lineCount > CODE_EXPAND_LINE_THRESHOLD
      ? '<div class="md-code__footer"><button type="button" class="md-code__expand" data-expand aria-expanded="false">Show more</button></div>'
      : ''

  return `<div class="md-code" data-block="${ordinal}">${header}${body}${footer}</div>`
}

// Images embed through the app's own proxy so the reader's browser never contacts
// the third party (ADR-0051). Anything that is not an absolute http(s) URL —
// including data: URIs — is dropped.
md.renderer.rules.image = (tokens, idx, options, env, self): string => {
  const token = tokens[idx]!
  const raw = token.attrGet('src')
  const source = raw == null ? '' : String(raw)
  let url: URL
  try {
    url = new URL(source)
  } catch {
    return ''
  }
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return ''

  const alt = self.renderInlineAsText(token.children ?? [], options, env)
  const src = `/api/v1/media/image?url=${encodeURIComponent(url.href)}`
  return `<img src="${md.utils.escapeHtml(src)}" alt="${md.utils.escapeHtml(alt)}" loading="lazy">`
}

// Links open in a new tab and never hand the opener to the target.
const defaultLinkOpen = md.renderer.rules.link_open
md.renderer.rules.link_open = (tokens, idx, options, env, self): string => {
  tokens[idx]!.attrSet('target', '_blank')
  tokens[idx]!.attrSet('rel', 'noopener noreferrer')
  return defaultLinkOpen
    ? defaultLinkOpen(tokens, idx, options, env, self)
    : self.renderToken(tokens, idx, options)
}

/**
 * Parse, sanitise, and return the assistant's rendered HTML. Raw HTML is escaped
 * by the parser and the result is sanitised again, so rendered content can never
 * execute code.
 */
export function renderAssistantMarkdown(text: string): string {
  const html = md.render(text, { blockOrdinal: 0, openFence: lastFenceIsOpen(text) })
  return DOMPurify.sanitize(html, {
    ADD_ATTR: ['target', 'rel', 'loading', 'data-block', 'data-copy', 'data-expand'],
  })
}

export type UserSegment = { type: 'text'; text: string } | { type: 'code'; text: string }

/**
 * Split a user message into literal text and fenced code segments. Everything is
 * literal except a fenced block; an unclosed fence runs to the end of the text.
 */
export function segmentUserText(text: string): UserSegment[] {
  const segments: UserSegment[] = []
  let textLines: string[] = []
  let codeLines: string[] = []
  let marker: string | null = null

  for (const line of text.split('\n')) {
    const match = line.match(/^\s*(`{3,}|~{3,})/)
    if (marker === null && match) {
      // A fence opens here: flush the literal run that preceded it.
      if (textLines.length > 0) {
        segments.push({ type: 'text', text: textLines.join('\n') })
        textLines = []
      }
      marker = match[1]![0]!
      codeLines = []
    } else if (marker !== null && match && match[1]![0] === marker) {
      segments.push({ type: 'code', text: codeLines.join('\n') })
      marker = null
      codeLines = []
    } else if (marker === null) {
      textLines.push(line)
    } else {
      codeLines.push(line)
    }
  }

  if (marker !== null) {
    segments.push({ type: 'code', text: codeLines.join('\n') })
  } else if (textLines.length > 0) {
    segments.push({ type: 'text', text: textLines.join('\n') })
  }

  return segments
}
