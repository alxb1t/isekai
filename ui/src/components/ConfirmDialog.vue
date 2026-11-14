<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useKeys } from '../composables/useKeys'
import { useHeldFocus } from '../composables/useHeldFocus'
import { plain } from '../stores/keys'
import KeyHint from './KeyHint.vue'

/* A question asked before something is deleted or removed. *No* comes first and holds the
   focus, so a stray `↵` does nothing; `h` `l` move, `↵` presses, `Esc` is *No*. A refusal
   is shown here and the focus goes back to *No*. `marker` names the `data-<marker>-…`
   attributes the tests read. */
const props = defineProps<{
  title: string
  name: string | null
  marker: string
  run: () => Promise<unknown>
}>()
const emit = defineEmits<{ close: []; done: [] }>()
const dialog = ref<HTMLDialogElement | null>(null)
const no = ref<HTMLButtonElement | null>(null)
const yes = ref<HTMLButtonElement | null>(null)
const refusal = ref<string | null>(null)
const running = ref(false)

const marked = (part: string): Record<string, string> => ({ [`data-${props.marker}-${part}`]: '' })

useHeldFocus(dialog, () => emit('close'))
onMounted(() => {
  dialog.value?.showModal()
  no.value?.focus()
})

const focused = () =>
  [no.value, yes.value].find((one) => one !== null && one === document.activeElement) ?? null

async function confirm(): Promise<void> {
  if (running.value) return
  running.value = true
  refusal.value = null
  try {
    await props.run()
    emit('done')
  } catch (reason) {
    refusal.value = (reason as Error).message
    no.value?.focus()
  } finally {
    running.value = false
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
    :aria-label="title"
    v-bind="marked('dialog')"
    @cancel.prevent
  >
    <header class="render-dialog__head">
      <h2 class="render-dialog__title">{{ title }}</h2>
      <p v-if="name" class="render-dialog__name mono" v-bind="marked('name')">{{ name }}</p>
    </header>
    <p v-if="refusal" class="large__refusal" v-bind="marked('refusal')">
      <span class="refusal__mark" />{{ refusal }}
    </p>
    <footer class="render-dialog__actions">
      <button
        ref="no"
        class="btn btn-secondary"
        type="button"
        v-bind="{ ...marked('choice'), ...marked('no') }"
        @click="emit('close')"
      >
        No<KeyHint command="cancel" />
      </button>
      <button
        ref="yes"
        class="btn btn-secondary"
        type="button"
        v-bind="{ ...marked('choice'), ...marked('yes') }"
        @click="confirm"
      >
        Yes
      </button>
    </footer>
  </dialog>
</template>
