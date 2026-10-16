<script setup lang="ts">
/**
 * The account's standing instructions and response style (FR-24, FR-25), as a
 * section of the settings dialog. Both shape future replies only: nothing here
 * rewrites a message already in a transcript, which is what the copy under the
 * fields says rather than something the reader has to assume.
 */
import Button from 'primevue/button'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import { computed, ref, watch } from 'vue'

import { useSessionStore } from '@/features/auth'
import { ApiError } from '@/lib/api'
import {
  INSTRUCTIONS_MAX_LENGTH,
  RESPONSE_STYLE_OPTIONS,
  type ResponseStyle,
} from '@/lib/preferences'
import { updatePreferences } from '../api'

const session = useSessionStore()

const instructions = ref('')
const style = ref<ResponseStyle>('default')
const saving = ref(false)
const saved = ref(false)
const error = ref('')

/** The stored values, which are what the form's dirty check compares against. */
const stored = computed(() => ({
  instructions: session.user?.instructions ?? '',
  response_style: session.user?.response_style ?? 'default',
}))

const dirty = computed(
  () =>
    instructions.value.trim() !== stored.value.instructions ||
    style.value !== stored.value.response_style,
)
const canSave = computed(() => dirty.value && !saving.value)

// The form opens on the stored values and re-reads them whenever the session's
// user changes — which is what a save does, so the two cannot drift.
watch(
  () => session.user,
  (user) => {
    instructions.value = user?.instructions ?? ''
    style.value = user?.response_style ?? 'default'
  },
  { immediate: true },
)

// The field enforces the cap the API enforces, so a value that could not be
// saved cannot be typed. `maxlength` covers typing; this covers every other way
// a value reaches the field.
watch(instructions, (value) => {
  if (value.length > INSTRUCTIONS_MAX_LENGTH) {
    instructions.value = value.slice(0, INSTRUCTIONS_MAX_LENGTH)
  }
})

// Editing retires the message about the last save; it described a value this
// one is no longer.
watch([instructions, style], () => {
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
  const trimmed = instructions.value.trim()
  try {
    await updatePreferences({ instructions: trimmed, response_style: style.value })
    // The field shows what was stored, and the session's user is refetched so
    // every reader of it — this form included — sees the same values.
    instructions.value = trimmed
    await session.refresh()
    saved.value = true
  } catch (failure) {
    error.value = failure instanceof ApiError ? failure.message : 'Could not save your preferences.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="space-y-1.5">
      <div class="flex items-baseline justify-between gap-3">
        <label for="personalization-instructions" class="text-body-sm font-medium text-ink">
          Instructions
        </label>
        <span id="personalization-counter" class="font-mono text-caption text-subtext">
          {{ instructions.length }}/{{ INSTRUCTIONS_MAX_LENGTH }}
        </span>
      </div>
      <Textarea
        id="personalization-instructions"
        v-model="instructions"
        fluid
        rows="4"
        :maxlength="INSTRUCTIONS_MAX_LENGTH"
        aria-describedby="personalization-counter"
        placeholder="Notes the assistant should keep in mind, in every conversation."
      />
      <p class="text-body-sm text-subtext">
        Applied to future replies. Nothing already said is rewritten.
      </p>
    </div>

    <div class="space-y-1.5">
      <label for="personalization-style" class="text-body-sm font-medium text-ink">
        Response style
      </label>
      <Select
        v-model="style"
        input-id="personalization-style"
        fluid
        :options="RESPONSE_STYLE_OPTIONS"
        option-label="label"
        option-value="value"
      />
      <p class="text-body-sm text-subtext">How replies are worded, not what they say.</p>
    </div>

    <div class="flex items-center gap-3">
      <Button label="Save" size="small" :disabled="!canSave" :loading="saving" @click="save" />
      <p v-if="error" role="alert" class="text-body-sm text-danger">{{ error }}</p>
      <p v-else-if="saved" role="status" class="text-body-sm text-subtext">Saved.</p>
    </div>
  </div>
</template>
