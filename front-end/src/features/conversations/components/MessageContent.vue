<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

import { renderAssistantMarkdown, segmentUserText } from '../markdown'

const props = defineProps<{ role: 'user' | 'assistant'; text: string }>()

const html = computed(() => (props.role === 'assistant' ? renderAssistantMarkdown(props.text) : ''))
const segments = computed(() => (props.role === 'user' ? segmentUserText(props.text) : []))

const root = ref<HTMLElement | null>(null)

// Interactive state is kept outside the rendered string and re-applied after
// every update, so it survives the re-render each streamed chunk triggers.
const expandedBlocks = new Set<number>()
let copiedBlock: number | null = null
let copyTimer: ReturnType<typeof setTimeout> | undefined

/**
 * Copy text, preferring the async Clipboard API and falling back to the legacy
 * `execCommand` path where that API is unavailable — which is any non-secure
 * origin, including the containerized e2e stack's `http://caddy`.
 */
async function copyToClipboard(text: string): Promise<boolean> {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch {
      // Fall through to the legacy path.
    }
  }

  const area = document.createElement('textarea')
  area.value = text
  area.setAttribute('readonly', '')
  area.style.position = 'fixed'
  area.style.opacity = '0'
  document.body.appendChild(area)
  area.select()
  const copied = document.execCommand('copy')
  document.body.removeChild(area)
  return copied
}

function applyState(): void {
  const container = root.value
  if (!container) return
  for (const block of container.querySelectorAll<HTMLElement>('.md-code[data-block]')) {
    const ordinal = Number(block.dataset.block)
    const isExpanded = expandedBlocks.has(ordinal)
    block.classList.toggle('is-expanded', isExpanded)

    const expand = block.querySelector<HTMLElement>('.md-code__expand')
    if (expand) {
      expand.setAttribute('aria-expanded', String(isExpanded))
      expand.textContent = isExpanded ? 'Show less' : 'Show more'
    }

    const copy = block.querySelector<HTMLElement>('.md-code__copy')
    if (copy) copy.toggleAttribute('data-copied', copiedBlock === ordinal)
  }
}

function onClick(event: MouseEvent): void {
  const target = event.target as HTMLElement

  const copyButton = target.closest<HTMLElement>('[data-copy]')
  if (copyButton) {
    const block = copyButton.closest<HTMLElement>('.md-code')
    const code = block?.querySelector('code')
    if (block && code) {
      const ordinal = Number(block.dataset.block)
      void copyToClipboard(code.textContent ?? '').then((copied) => {
        if (!copied) return
        copiedBlock = ordinal
        applyState()
        clearTimeout(copyTimer)
        copyTimer = setTimeout(() => {
          copiedBlock = null
          applyState()
        }, 1500)
      })
    }
    return
  }

  const expandButton = target.closest<HTMLElement>('[data-expand]')
  if (expandButton) {
    const block = expandButton.closest<HTMLElement>('.md-code')
    if (!block) return
    const ordinal = Number(block.dataset.block)
    if (expandedBlocks.has(ordinal)) expandedBlocks.delete(ordinal)
    else expandedBlocks.add(ordinal)
    applyState()
  }
}

watch(html, () => {
  void nextTick(applyState)
})

onBeforeUnmount(() => {
  clearTimeout(copyTimer)
})
</script>

<template>
  <p
    v-if="role === 'user'"
    class="max-w-[85%] overflow-hidden rounded-xl bg-line/60 px-4 py-2.5 text-body leading-relaxed text-ink"
  >
    <template v-for="(segment, index) in segments" :key="index">
      <span
        v-if="segment.type === 'text'"
        class="block whitespace-pre-wrap [overflow-wrap:anywhere]"
        >{{ segment.text }}</span
      >
      <code
        v-else
        class="mt-2 block overflow-x-auto rounded-lg bg-paper-white/70 p-3 font-mono text-body-sm whitespace-pre"
        >{{ segment.text }}</code
      >
    </template>
  </p>
  <div
    v-else
    ref="root"
    class="markdown w-full text-body text-ink"
    @click="onClick"
    v-html="html"
  />
</template>

<style scoped>
.markdown {
  line-height: 1.5;
}

.markdown :deep(p) {
  margin: 0 0 12px;
}
.markdown :deep(p:last-child) {
  margin-bottom: 0;
}
.markdown :deep(h1),
.markdown :deep(h2),
.markdown :deep(h3),
.markdown :deep(h4),
.markdown :deep(h5),
.markdown :deep(h6) {
  font-weight: 600;
  margin: 18px 0 8px;
}
.markdown :deep(h1),
.markdown :deep(h2) {
  font-size: 20px;
}
.markdown :deep(h3),
.markdown :deep(h4),
.markdown :deep(h5),
.markdown :deep(h6) {
  font-size: 18px;
}
.markdown :deep(ul),
.markdown :deep(ol) {
  margin: 0 0 12px;
  padding-left: 20px;
}
.markdown :deep(li) {
  margin-bottom: 6px;
}
.markdown :deep(ul) {
  list-style: disc;
}
.markdown :deep(ol) {
  list-style: decimal;
}
.markdown :deep(blockquote) {
  border-left: 2px solid var(--color-line);
  padding-left: 12px;
  margin: 0 0 12px;
  color: var(--color-tertiary);
}
.markdown :deep(code) {
  background: color-mix(in srgb, var(--color-line) 60%, transparent);
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 0.9em;
  padding: 1px 4px;
}
.markdown :deep(a) {
  color: var(--color-tertiary);
  font-weight: 500;
  text-decoration: none;
}
.markdown :deep(a:hover) {
  color: var(--color-ink);
}
.markdown :deep(hr) {
  border: 0;
  border-top: 1px solid var(--color-line);
  margin: 16px 0;
}
.markdown :deep(table) {
  display: block;
  overflow-x: auto;
  width: 100%;
  border-collapse: collapse;
  margin: 0 0 12px;
}
.markdown :deep(th),
.markdown :deep(td) {
  border: 1px solid var(--color-line);
  padding: 8px 12px;
  text-align: left;
}
.markdown :deep(th) {
  background: color-mix(in srgb, var(--color-line) 40%, transparent);
  font-weight: 500;
}
.markdown :deep(img) {
  max-width: 100%;
  border: 1px solid var(--color-line);
  border-radius: 12px;
  margin: 12px 0;
}

/* Code block (DESIGN.md: Code Block) */
.markdown :deep(.md-code) {
  background: var(--color-paper-white);
  border: 1px solid var(--color-line);
  border-radius: 12px;
  margin: 4px 0 12px;
  overflow: hidden;
}
.markdown :deep(.md-code__header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-line);
}
.markdown :deep(.md-code__lang) {
  color: var(--color-subtext);
  font-size: 14px;
}
.markdown :deep(.md-code__copy) {
  color: var(--color-tertiary);
  border-radius: 8px;
  padding: 4px;
  display: inline-flex;
}
.markdown :deep(.md-code__copy:hover) {
  background: color-mix(in srgb, var(--color-line) 40%, transparent);
}
.markdown :deep(.md-code__check) {
  display: none;
}
.markdown :deep(.md-code__copy[data-copied] .md-code__icon) {
  display: none;
}
.markdown :deep(.md-code__copy[data-copied] .md-code__check) {
  display: inline;
}
.markdown :deep(.md-code__body) {
  margin: 0;
  max-height: 24rem;
  overflow: auto;
  padding: 12px;
  font-family: var(--font-mono);
  font-size: 14px;
  line-height: 1.5;
}
.markdown :deep(.md-code.is-expanded .md-code__body) {
  max-height: none;
}
.markdown :deep(.md-code__body code) {
  background: none;
  padding: 0;
  font-size: inherit;
  border-radius: 0;
}
.markdown :deep(.md-code__footer) {
  border-top: 1px solid var(--color-line);
  padding: 8px 12px;
}
.markdown :deep(.md-code__expand) {
  color: var(--color-tertiary);
  font-size: 14px;
}
.markdown :deep(.hljs) {
  background: transparent;
}
</style>
