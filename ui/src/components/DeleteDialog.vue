<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { type RenderPlace, deleteRender } from '../api'
import { useKeys } from '../composables/useKeys'
import { useHeldFocus } from '../composables/useHeldFocus'
import { plain } from '../stores/keys'
import KeyHint from './KeyHint.vue'

/* *Delete this render?* asks before a large view's render is deleted. *No* comes
   first and holds the focus, so a stray `↵` deletes nothing; `h` `l` move, `↵`
   presses, `Esc` is *No*. A refusal is shown here and the focus goes back to *No*. */
const props = defineProps<{ place: RenderPlace }>()
const emit = defineEmits<{ close: []; deleted: [] }>()
const dialog = ref<HTMLDialogElement | null>(null)
const no = ref<HTMLButtonElement | null>(null)
const yes = ref<HTMLButtonElement | null>(null)
const refusal = ref<string | null>(null)
const deleting = ref(false)

useHeldFocus(dialog, () => emit('close'))
onMounted(() => {
  dialog.value?.showModal()
  no.value?.focus()
})

const focused = () =>
  [no.value, yes.value].find((one) => one !== null && one === document.activeElement) ?? null

async function confirm(): Promise<void> {
  if (deleting.value) return
  deleting.value = true
  refusal.value = null
  try {
    await deleteRender(props.place)
    emit('deleted')
  } catch (reason) {
    refusal.value = (reason as Error).message
    no.value?.focus()
  } finally {
    deleting.value = false
  }
}

useKeys('overlay', [
  { id: 'cancel', keys: plain('Escape'), label: 'no', run: () => emit('close') },
  {
    id: 'previous',
    keys: plain('KeyH', 'ArrowLeft'),
    label: 'focus no',
    run: () => no.value?.focus(),
  },
  {
    id: 'next',
    keys: plain('KeyL', 'ArrowRight'),
    label: 'focus yes',
    run: () => yes.value?.focus(),
  },
  {
    id: 'press',
    keys: plain('Enter'),
    label: 'press the focused choice',
    run: () => focused()?.click(),
    when: () => focused() !== null,
  },
])
</script>

<template>
  <dialog
    ref="dialog"
    class="render-dialog"
    aria-label="Delete this render?"
    data-delete-dialog
    @cancel.prevent
  >
    <header class="render-dialog__head">
      <h2 class="render-dialog__title">Delete this render?</h2>
    </header>
    <p v-if="refusal" class="renders__refusal" data-delete-refusal>
      <span class="refusal__mark" />{{ refusal }}
    </p>
    <footer class="render-dialog__actions">
      <button
        ref="no"
        class="btn btn-secondary"
        type="button"
        data-delete-choice
        data-delete-no
        @click="emit('close')"
      >
        No<KeyHint command="cancel" />
      </button>
      <button
        ref="yes"
        class="btn btn-secondary"
        type="button"
        data-delete-choice
        data-delete-yes
        @click="confirm"
      >
        Yes
      </button>
    </footer>
  </dialog>
</template>
