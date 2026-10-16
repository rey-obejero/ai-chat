<script setup lang="ts">
/**
 * The account's name (FR-7), as a section of the settings dialog: the same field
 * the first-run prompt asks with, on the same stored value, so a name set here is
 * the one the prompt would have set.
 */
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { computed, nextTick, ref, watch } from 'vue'

import { useSessionStore } from '@/features/auth'
import { ApiError } from '@/lib/api'
import { DISPLAY_NAME_MAX_LENGTH } from '@/lib/display-name'

const session = useSessionStore()

const name = ref('')
const saving = ref(false)
const saved = ref(false)
const error = ref('')

/** The stored name, which is what the form's dirty check compares against. */
const stored = computed(() => session.user?.display_name ?? '')
const trimmed = computed(() => name.value.trim())
const dirty = computed(() => trimmed.value !== stored.value)
const canSave = computed(() => dirty.value && trimmed.value.length > 0 && !saving.value)

/**
 * The field's own complaint, which is only worth making once the value differs
 * from the stored one: a cleared field is a problem the reader just made, while
 * an untouched field is not a problem at all.
 */
const validation = computed(() =>
  dirty.value && trimmed.value.length === 0 ? 'A name is required, or keep the one you have.' : '',
)

// The form opens on the stored value and re-reads it whenever the session's user
// changes — which is what a save does, so the two cannot drift.
watch(
  () => session.user,
  (user) => {
    name.value = user?.display_name ?? ''
  },
  { immediate: true },
)

// The field enforces the cap the API enforces, so a name that could not be saved
// cannot be typed. `maxlength` covers typing; this covers every other way a value
// reaches the field.
watch(name, (value) => {
  if (value.length > DISPLAY_NAME_MAX_LENGTH) {
    name.value = value.slice(0, DISPLAY_NAME_MAX_LENGTH)
  }
})

// Editing retires the messages about the last save; they described a value this
// one is no longer.
watch(name, () => {
  saved.value = false
  error.value = ''
})

async function save(): Promise<void> {
  if (!canSave.value) {
    return
  }

  saving.value = true
  saved.value = false
  error.value = ''
  const next = trimmed.value
  try {
    // The session's user is replaced with what the API stored, so this field and
    // the account button that reads the same user show the same name.
    await session.saveDisplayName(next)
    name.value = next
    // Writing the field stops the form being dirty, and the edit it counts as
    // retires the last message; the confirmation describes the name just stored,
    // so it is written once that has settled.
    await nextTick()
    saved.value = true
  } catch (failure) {
    error.value = failure instanceof ApiError ? failure.message : 'Could not save your name.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="space-y-1.5">
      <label for="profile-name" class="text-body-sm font-medium text-ink">Name</label>
      <InputText
        id="profile-name"
        v-model="name"
        fluid
        autocomplete="nickname"
        :maxlength="DISPLAY_NAME_MAX_LENGTH"
        aria-describedby="profile-name-hint"
      />
      <p v-if="validation" role="alert" class="text-body-sm text-danger">{{ validation }}</p>
      <p id="profile-name-hint" class="text-body-sm text-subtext">Shown on your account.</p>
    </div>

    <div class="flex items-center gap-3">
      <Button label="Save" size="small" :disabled="!canSave" :loading="saving" @click="save" />
      <p v-if="error" role="alert" class="text-body-sm text-danger">{{ error }}</p>
      <p v-else-if="saved" role="status" class="text-body-sm text-subtext">Saved.</p>
    </div>
  </div>
</template>
