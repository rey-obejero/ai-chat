import { describe, expect, it } from 'vitest'

import { renderAssistantMarkdown, segmentUserText } from '@/features/conversations/markdown'

describe('renderAssistantMarkdown', () => {
  it('renders block markup as HTML', () => {
    const html = renderAssistantMarkdown(
      '# Title\n\n- one\n- two\n\n> quote\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n[link](https://example.com)',
    )

    expect(html).toContain('<h1>Title</h1>')
    expect(html).toContain('<ul>')
    expect(html).toContain('<blockquote>')
    expect(html).toContain('<table>')
    expect(html).toContain('href="https://example.com"')
    expect(html).toContain('rel="noopener noreferrer"')
    expect(html).toContain('target="_blank"')
  })

  it('highlights a closed fence and labels its language', () => {
    const html = renderAssistantMarkdown('```js\nconst answer = 1\n```')

    expect(html).toContain('class="md-code__lang">js<')
    expect(html).toContain('hljs-keyword')
  })

  it('renders an unclosed fence as plain code without breaking the text', () => {
    const html = renderAssistantMarkdown('before\n\n```js\nconst answer = 1')

    expect(html).toContain('before')
    expect(html).toContain('md-code')
    expect(html).not.toContain('hljs-keyword')
  })

  it('renders an unknown language plain but keeps its label', () => {
    const html = renderAssistantMarkdown('```brainfuck\n+++\n```')

    expect(html).toContain('class="md-code__lang">brainfuck<')
    expect(html).not.toContain('hljs-keyword')
  })

  it('linkifies bare URLs and refuses script protocols', () => {
    expect(renderAssistantMarkdown('see https://example.com')).toContain(
      '<a href="https://example.com"',
    )
    // The unsafe protocol is refused, so no anchor is produced and the text
    // stays literal and inert.
    expect(renderAssistantMarkdown('[x](javascript:alert(1))')).not.toContain('<a ')
  })

  it('escapes raw HTML instead of executing it', () => {
    const html = renderAssistantMarkdown('<img src=x onerror=alert(1)>')

    expect(html).not.toContain('<img')
    expect(html).not.toContain('<script')
    expect(html).toContain('&lt;img')
  })

  it('rewrites http(s) images through the proxy and keeps alt text', () => {
    const html = renderAssistantMarkdown('![diagram](https://example.com/x.png)')

    expect(html).toContain('src="/api/v1/media/image?url=')
    expect(html).toContain('alt="diagram"')
    expect(html).toContain('loading="lazy"')
  })

  it('drops non-http image sources', () => {
    const html = renderAssistantMarkdown('![a](data:image/png;base64,AAAA)')

    expect(html).not.toContain('<img')
  })

  it('adds the expand control only past the line threshold', () => {
    const long = `\`\`\`\n${Array.from({ length: 25 }, (_, i) => `line ${i}`).join('\n')}\n\`\`\``
    const short = '```\nline\n```'

    expect(renderAssistantMarkdown(long)).toContain('md-code__expand')
    expect(renderAssistantMarkdown(short)).not.toContain('md-code__expand')
  })

  it('never throws on malformed input', () => {
    expect(() => renderAssistantMarkdown('```\nunclosed [link]( and *stars **')).not.toThrow()
    expect(() => renderAssistantMarkdown('~~'.repeat(200))).not.toThrow()
  })
})

describe('segmentUserText', () => {
  it('splits literal text from a fenced block', () => {
    expect(segmentUserText('hello\n```\ncode here\n```\nworld')).toEqual([
      { type: 'text', text: 'hello' },
      { type: 'code', text: 'code here' },
      { type: 'text', text: 'world' },
    ])
  })

  it('preserves inner newlines and treats an unclosed fence as code', () => {
    expect(segmentUserText('a\n```\nline 1\nline 2')).toEqual([
      { type: 'text', text: 'a' },
      { type: 'code', text: 'line 1\nline 2' },
    ])
  })
})
