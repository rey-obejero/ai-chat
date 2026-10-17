<script setup lang="ts">
/**
 * The one-time name prompt (FR-7). The conversations view renders it only while
 * the account has not answered it, and Save and Skip are the only way out: the
 * dialog has no close control, and Escape and a click on the mask do nothing,
 * because dismissing it without answering would leave the flag unset and the
 * prompt would return on the next sign-in.
 */
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import { computed, ref, watch } from 'vue'

import { useSessionStore } from '@/features/auth'
import { ApiError } from '@/lib/api'
import { DISPLAY_NAME_MAX_LENGTH, displayNameOf } from '@/lib/display-name'

const session = useSessionStore()

/** Prefilled with the name the account already has, which is never blank. */
const name = ref(displayNameOf(session.user))
const saving = ref(false)
const skipping = ref(false)
const error = ref('')

const busy = computed(() => saving.value || skipping.value)
const trimmed = computed(() => name.value.trim())
const canSave = computed(() => trimmed.value.length > 0 && !busy.value)

// The field enforces the cap the API enforces, so a name that could not be
// saved cannot be typed. `maxlength` covers typing; this covers every other way
// a value reaches the field.
watch(name, (value) => {
  if (value.length > DISPLAY_NAME_MAX_LENGTH) {
    name.value = value.slice(0, DISPLAY_NAME_MAX_LENGTH)
  }
})

// Editing retires the message about the last refusal; it described a value this
// one is no longer.
watch(name, () => {
  error.value = ''
})

async function save(): Promise<void> {
  if (!canSave.value) {
    return
  }

  saving.value = true
  error.value = ''
  try {
    await session.saveDisplayName(trimmed.value)
  } catch (failure) {
    error.value = failure instanceof ApiError ? failure.message : 'Could not save your name.'
  } finally {
    saving.value = false
  }
}

async function skip(): Promise<void> {
  if (busy.value) {
    return
  }

  skipping.value = true
  error.value = ''
  try {
    await session.skipNamePrompt()
  } catch (failure) {
    error.value = failure instanceof ApiError ? failure.message : 'Could not skip for now.'
  } finally {
    skipping.value = false
  }
}
</script>

<template>
  <Dialog
    :visible="true"
    modal
    header="What should we call you?"
    :closable="false"
    :close-on-escape="false"
    :dismissable-mask="false"
    class="w-full max-w-md !bg-paper-white !text-ink"
  >
    <div class="space-y-4">
      <p class="text-body-sm text-subtext">
        This is the name shown on your account. It starts as the one taken from your email.
      </p>

      <div class="space-y-1.5">
        <label for="name-prompt-name" class="text-body-sm font-medium text-ink">Name</label>
        <InputText
          id="name-prompt-name"
          v-model="name"
          fluid
          autofocus
          autocomplete="nickname"
          :maxlength="DISPLAY_NAME_MAX_LENGTH"
          @keydown.enter="save"
        />
        <p v-if="error" role="alert" class="text-body-sm text-danger">{{ error }}</p>
      </div>

      <div class="flex items-center gap-3">
        <Button label="Save" size="small" :disabled="!canSave" :loading="saving" @click="save" />
        <Button label="Skip" text size="small" :disabled="busy" :loading="skipping" @click="skip" />
      </div>
    </div>
  </Dialog>
</template>
