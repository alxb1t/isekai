<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref } from 'vue'
import { useHeldFocus } from '../composables/useHeldFocus'
import { useKeys } from '../composables/useKeys'
import { KEY_LIST, plain, useKeyStore } from '../stores/keys'
import KeyHint from './KeyHint.vue'

/* Every key this screen answers, in a modal dialog that holds the focus: a column
   per scope, everywhere's then the screen's, read from their declarations. */
const emit = defineEmits<{ close: [] }>()
const dialog = ref<HTMLDialogElement | null>(null)
const { listed } = storeToRefs(useKeyStore())

const COLUMNS = [
  { scope: 'everywhere', title: 'everywhere' },
  { scope: 'screen', title: 'this screen' },
] as const
const columns = computed(() =>
  COLUMNS.map((column) => ({
    ...column,
    entries: listed.value.filter((one) => one.scope === column.scope),
  })).filter((column) => column.entries.length > 0),
)

const close = () => dialog.value?.close()

useKeys('overlay', [
  { id: 'close', keys: [...plain('Escape'), KEY_LIST], label: 'close', run: close },
])

useHeldFocus(dialog, close)
onMounted(() => dialog.value?.showModal())
</script>

<template>
  <dialog
    ref="dialog"
    class="keys-dialog"
    aria-label="the key list"
    data-key-list
    @close="emit('close')"
  >
    <div class="overlay__controls">
      <span class="kicker">keys</span>
      <span class="overlay__exit mono"><KeyHint command="close" /> · click outside</span>
    </div>
    <div class="keys-dialog__columns">
      <section
        v-for="column in columns"
        :key="column.scope"
        class="keys-dialog__column"
        :data-scope="column.scope"
      >
        <span class="section-label">{{ column.title }}</span>
        <dl class="keylist mono">
          <template v-for="(one, index) in column.entries" :key="index">
            <dt class="keylist__keys">{{ one.keys }}</dt>
            <dd class="keylist__label">{{ one.label }}</dd>
          </template>
        </dl>
      </section>
    </div>
  </dialog>
</template>
