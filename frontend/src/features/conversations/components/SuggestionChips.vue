<script setup lang="ts">
import type { Component } from 'vue'

import IconAlignLeft from '~icons/lucide/align-left'
import IconBrain from '~icons/lucide/brain'
import IconChartColumn from '~icons/lucide/chart-column'
import IconCode from '~icons/lucide/code'
import IconLightbulb from '~icons/lucide/lightbulb'
import IconListChecks from '~icons/lucide/list-checks'
import IconNotebookPen from '~icons/lucide/notebook-pen'
import IconRefreshCw from '~icons/lucide/refresh-cw'

const emit = defineEmits<{ select: [prompt: string] }>()

// Each chip seeds the composer with a starter prompt; nothing is sent on click.
const suggestions: { label: string; icon: Component; prompt: string }[] = [
  {
    label: 'Write',
    icon: IconNotebookPen,
    prompt: 'Write a first draft of a short introduction to ',
  },
  {
    label: 'Revise',
    icon: IconRefreshCw,
    prompt: 'Revise the following text for clarity and tone: ',
  },
  {
    label: 'Summarize',
    icon: IconAlignLeft,
    prompt: 'Summarize the key points of the following: ',
  },
  {
    label: 'Explain',
    icon: IconLightbulb,
    prompt: 'Explain the following concept in simple terms: ',
  },
  { label: 'Brainstorm', icon: IconBrain, prompt: 'Brainstorm ten ideas for ' },
  {
    label: 'Analyze',
    icon: IconChartColumn,
    prompt: 'Analyze the following and highlight the main risks: ',
  },
  { label: 'Plan', icon: IconListChecks, prompt: 'Plan a step-by-step approach to ' },
  { label: 'Code', icon: IconCode, prompt: 'Write a TypeScript function that ' },
]
</script>

<template>
  <ul class="flex flex-wrap items-center justify-center gap-1.5">
    <li v-for="item in suggestions" :key="item.label">
      <button
        type="button"
        class="flex cursor-pointer items-center gap-1.5 rounded-lg border border-line bg-transparent px-2.5 py-1.5 text-body-sm text-ink transition-colors hover:bg-line/40 active:bg-line/60 motion-reduce:transition-none"
        @click="emit('select', item.prompt)"
      >
        <component :is="item.icon" class="size-3.5 shrink-0 text-icon" stroke-width="2" />
        <span>{{ item.label }}</span>
      </button>
    </li>
  </ul>
</template>
