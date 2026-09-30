<script setup lang="ts">
import Button from 'primevue/button'

import IconBlocks from '~icons/lucide/blocks'
import IconCirclePlus from '~icons/lucide/circle-plus'
import IconLibrary from '~icons/lucide/library'
import IconMessageCircleDashed from '~icons/lucide/message-circle-dashed'
import IconSearch from '~icons/lucide/search'
import IconSidebar from '~icons/lucide/sidebar'
import IconSparkles from '~icons/lucide/sparkles'

import BrandLogo from '@/components/BrandLogo.vue'
import AppHeader from './AppHeader.vue'
import NavItem from './NavItem.vue'

const collapsed = defineModel<boolean>('collapsed', { required: true })

// Hover or keyboard focus over the header swaps the logo for the expand
// toggle. Driven by state rather than a `group-hover` utility so it also
// responds to keyboard focus.
const emit = defineEmits<{ newConversation: [] }>()

// The sidebar rows are a fixed list, so they are written out rather than mapped.
// Only "New conversation" is wired; the rest are inert by design.
const INERT = ['Search', 'Plugins', 'Skills', 'Library']
const INERT_ICONS = [IconSearch, IconBlocks, IconSparkles, IconLibrary]
</script>

<template>
  <div class="flex h-screen bg-paper-white text-ink">
    <aside
      id="sidebar"
      class="flex shrink-0 flex-col border-r border-line bg-canvas transition-[width] duration-200 ease-out motion-reduce:transition-none"
      :class="collapsed ? 'w-16' : 'w-64 max-sm:w-16'"
    >
      <div
        class="flex h-14 shrink-0 items-center px-2"
        :class="collapsed ? 'justify-center' : 'justify-between'"
      >
        <!-- The logo is always present. When the rail is collapsed there is no
             room for it and the toggle side by side, so the toggle takes the
             logo's place and appears on hover or keyboard focus. Driven by CSS
             :hover rather than state: collapsing removes the clicked button from
             under the pointer, which fires a mouseleave and would immediately
             hide the toggle the user has just moved to. -->
        <div class="logo-slot relative flex size-8 items-center justify-center">
          <!-- Flex, not a plain block: a block wrapper puts the logo on a text
               baseline and leaves descender space under it, so the glyph sits a
               few pixels high and the toggle appears to hang low over it. -->
          <span
            class="logo-mark flex items-center justify-center transition-opacity motion-reduce:transition-none"
          >
            <BrandLogo />
          </span>
          <Button
            v-if="collapsed"
            text
            rounded
            aria-label="Expand sidebar"
            :aria-expanded="!collapsed"
            aria-controls="sidebar"
            class="expand-toggle !absolute !size-8 !p-0 opacity-0 transition-opacity focus-visible:ring-2 focus-visible:ring-ink motion-reduce:transition-none"
            v-tooltip="{ value: 'Expand sidebar', class: 'text-body-sm' }"
            @click="collapsed = false"
          >
            <IconSidebar class="size-4 shrink-0 text-icon" stroke-width="2" />
          </Button>
        </div>
        <Button
          v-if="!collapsed"
          text
          rounded
          aria-label="Collapse sidebar"
          :aria-expanded="!collapsed"
          aria-controls="sidebar"
          class="!size-8 shrink-0 !p-0 max-sm:hidden"
          v-tooltip="{ value: 'Collapse sidebar', class: 'text-body-sm' }"
          @click="collapsed = true"
        >
          <IconSidebar class="size-4 shrink-0 text-icon" stroke-width="2" />
        </Button>
      </div>

      <nav class="space-y-0.5 px-2">
        <NavItem
          label="New conversation"
          :icon="IconCirclePlus"
          variant="filled"
          :collapsed="collapsed"
          v-tooltip="{ value: collapsed ? 'New conversation' : null, class: 'text-body-sm' }"
          @select="emit('newConversation')"
        />
        <NavItem
          v-for="(label, index) in INERT"
          :key="label"
          :label="label"
          :icon="INERT_ICONS[index]!"
          :collapsed="collapsed"
          v-tooltip="{ value: collapsed ? label : null, class: 'text-body-sm' }"
        />
      </nav>

      <!-- Collapsed, the rail carries navigation only; the grouped lists need
           the width their labels do. -->
      <div v-if="!collapsed" class="min-h-0 flex-1 overflow-y-auto px-2 pb-2 max-sm:hidden">
        <slot name="sidebar" />
      </div>
      <div v-else class="flex-1" />

      <div class="shrink-0 p-2">
        <slot name="account" :collapsed="collapsed" />
      </div>
    </aside>

    <main class="flex min-w-0 flex-1 flex-col bg-canvas">
      <AppHeader>
        <template #title>
          <slot name="title" />
        </template>
        <template #actions>
          <!-- Named apart from the sidebar's "New conversation" so the two
               do not share an accessible name. -->
          <Button
            text
            rounded
            aria-label="Temporary conversation"
            class="!size-8 !p-0"
            v-tooltip="{ value: 'Temporary conversation', class: 'text-body-sm' }"
          >
            <IconMessageCircleDashed class="size-4 shrink-0 text-icon" stroke-width="2" />
          </Button>
        </template>
      </AppHeader>

      <slot />
    </main>
  </div>
</template>

<style scoped>
/* Native :hover, not a `group-hover` utility: `group-hover` is inert in this
   build, and JS hover state is reset by the DOM swap on collapse. */
.logo-slot:hover .logo-mark,
.logo-slot:focus-within .logo-mark {
  opacity: 0;
}

.logo-slot:hover .expand-toggle,
.logo-slot:focus-within .expand-toggle {
  opacity: 1;
}
</style>
