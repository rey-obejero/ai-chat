<script setup lang="ts">
/**
 * The conversation rows (DESIGN.md — Conversation Row). Rows are presentation
 * only: selection arrives as `activeId` and every mutation leaves as an event,
 * because the store and the route live in the view. The trailing trigger's
 * reveal is the scoped CSS at the foot of this file: `group-*` is inert here.
 */
import Button from 'primevue/button'
import Menu from 'primevue/menu'
import type { MenuItem } from 'primevue/menuitem'
import { computed, nextTick, ref, type ComponentPublicInstance } from 'vue'

import IconMoreHorizontal from '~icons/lucide/more-horizontal'
import IconStar from '~icons/lucide/star'

import type { Conversation } from '../api'

const activeId = defineModel<string | null>('activeId')

const props = defineProps<{ conversations: Conversation[] }>()

const emit = defineEmits<{
  rename: [id: string, title: string]
  togglePin: [id: string]
  toggleFavourite: [id: string]
  toggleArchive: [id: string]
  /** The whole row, not its id: the confirmation names the conversation. */
  remove: [conversation: Conversation]
}>()

// One popup for the list, not one per row: it is opened from a row and holds
// that row as its target, the way the account menu holds the session.
const rowMenu = ref<InstanceType<typeof Menu> | null>(null)
const menuTarget = ref<Conversation | null>(null)

const renamingId = ref<string | null>(null)
const draftTitle = ref('')
const renameInput = ref<HTMLInputElement | null>(null)
// Function refs keyed by row: a `v-for` ref would collect into an array, and
// the title button is what takes focus back once an edit ends.
const titleButtons = new Map<string, HTMLButtonElement>()

const rowItems = computed<MenuItem[]>(() => {
  const target = menuTarget.value
  if (!target) {
    return []
  }
  return [
    { label: 'Rename', command: () => void startRenaming(target) },
    { label: target.is_pinned ? 'Unpin' : 'Pin', command: () => emit('togglePin', target.id) },
    {
      label: target.is_favourite ? 'Remove from favourites' : 'Add to favourites',
      command: () => emit('toggleFavourite', target.id),
    },
    {
      label: target.is_archived ? 'Unarchive' : 'Archive',
      command: () => emit('toggleArchive', target.id),
    },
    { separator: true },
    { label: 'Delete', command: () => emit('remove', target) },
  ]
})

function openMenu(event: Event, conversation: Conversation): void {
  menuTarget.value = conversation
  rowMenu.value?.toggle(event)
}

function setTitleButton(id: string, el: Element | ComponentPublicInstance | null): void {
  if (el instanceof HTMLButtonElement) {
    titleButtons.set(id, el)
  } else {
    titleButtons.delete(id)
  }
}

function setRenameInput(el: Element | ComponentPublicInstance | null): void {
  renameInput.value = el instanceof HTMLInputElement ? el : null
}

async function startRenaming(conversation: Conversation): Promise<void> {
  renamingId.value = conversation.id
  draftTitle.value = conversation.title
  await nextTick()
  renameInput.value?.focus()
  renameInput.value?.select()
}

/** The field is on its way out, so focus has to be handed back deliberately. */
async function endRenaming(id: string): Promise<void> {
  renamingId.value = null
  await nextTick()
  titleButtons.get(id)?.focus()
}

function commitRename(): void {
  const conversation = props.conversations.find((item) => item.id === renamingId.value)
  if (!conversation) {
    return
  }
  const title = draftTitle.value.trim()
  // A blank title is what the API rejects (1–255 characters) and an unchanged
  // one is not worth a write, so both simply close the field.
  if (title.length > 0 && title !== conversation.title) {
    emit('rename', conversation.id, title)
  }
  void endRenaming(conversation.id)
}

function cancelRename(): void {
  if (renamingId.value) {
    void endRenaming(renamingId.value)
  }
}
</script>

<template>
  <div>
    <ul class="space-y-0.5">
      <li v-for="conversation in conversations" :key="conversation.id">
        <div
          class="conversation-row flex items-center rounded-lg pr-1 transition-colors motion-reduce:transition-none"
          :class="conversation.id === activeId ? 'bg-line/60' : 'hover:bg-line/40'"
        >
          <input
            v-if="renamingId === conversation.id"
            :ref="setRenameInput"
            v-model="draftTitle"
            type="text"
            class="mx-0.5 my-px min-w-0 flex-1 rounded-xl border border-line bg-paper-white px-2.5 py-1.5 text-body-sm text-ink focus:border-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
            aria-label="Conversation title"
            @keydown.enter.prevent="commitRename"
            @keydown.esc.prevent="cancelRename"
          />
          <button
            v-else
            :ref="(el) => setTitleButton(conversation.id, el)"
            type="button"
            class="min-w-0 flex-1 cursor-pointer truncate rounded-lg px-2.5 py-2 text-left text-body-sm transition-colors motion-reduce:transition-none"
            :class="[
              conversation.is_archived ? 'text-subtext' : 'text-ink',
              conversation.id === activeId ? 'font-medium' : '',
            ]"
            :aria-current="conversation.id === activeId ? 'true' : undefined"
            @click="activeId = conversation.id"
          >
            {{ conversation.title }}
            <!-- The Archived group's header names the state as well, but the row
                 is the thing that is announced; colour alone would not say it. -->
            <span v-if="conversation.is_archived" class="sr-only"> (archived)</span>
          </button>

          <span
            v-if="conversation.is_favourite"
            role="img"
            aria-label="Favourite"
            class="mr-0.5 flex size-4 shrink-0 items-center justify-center"
          >
            <IconStar class="size-3 text-icon" stroke-width="2" />
          </span>

          <Button
            text
            rounded
            aria-label="Conversation actions"
            aria-haspopup="true"
            class="row-menu-trigger !size-6 !p-0"
            v-tooltip="{ value: 'Conversation actions', class: 'text-body-sm' }"
            @click="openMenu($event, conversation)"
          >
            <IconMoreHorizontal class="size-4 shrink-0 text-icon" stroke-width="2" />
          </Button>
        </div>
      </li>
    </ul>

    <Menu ref="rowMenu" :model="rowItems" :popup="true" />
  </div>
</template>

<style scoped>
/* Revealed, not removed: the trigger keeps its 24px whether or not it is
   visible, so nothing moves when it appears, and it stays keyboard-focusable at
   rest — Tab into it and `:focus-within` brings it back. Native variants
   (`group-*` is inert in this build); a coarse pointer has no hover to reveal
   it, so there it is always shown. */
.conversation-row .row-menu-trigger {
  opacity: 0;
  pointer-events: none;
}

.conversation-row:hover .row-menu-trigger,
.conversation-row:focus-within .row-menu-trigger {
  opacity: 1;
  pointer-events: auto;
}

@media (pointer: coarse) {
  .conversation-row .row-menu-trigger {
    opacity: 1;
    pointer-events: auto;
  }
}
</style>
