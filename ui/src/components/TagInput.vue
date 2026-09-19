<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useVocabulary } from '../composables/useVocabulary'
import TagAutocomplete from './TagAutocomplete.vue'

/* The in-flight fragment, and the dropdown it opens.

   The fragment is **bare mono text with a 1px accent caret, never a chip**.
   Committed and in-flight must never look alike, which is why the caret border
   appears only while this input holds the focus.

   A fragment that matches nothing shows no rows and cannot be committed. There
   is no path to free text in a chip, and that is what underwrites two of the
   four refusal kinds this version defers: an out-of-vocabulary tag can only ever
   arrive from the sorter. */
const props = defineProps<{
  field: string
  vocabulary: number
  focused: boolean
  chips: number
  selected: number | null
}>()

const emit = defineEmits<{
  commit: [tag: string]
  focus: []
  blur: []
  back: []
  step: [direction: -1 | 1]
  row: [direction: -1 | 1]
}>()

const fragment = ref('')
const selected = ref(0)
const { matches, total, search, clear } = useVocabulary()

const open = computed(() => props.focused && matches.value.length > 0)

watch(fragment, (value) => {
  selected.value = 0
  search(value)
})

function reset(): void {
  fragment.value = ''
  selected.value = 0
  clear()
}

defineExpose({ reset, fragment })

function onKey(event: KeyboardEvent): void {
  if (event.key === 'ArrowDown' && open.value) {
    event.preventDefault()
    selected.value = (selected.value + 1) % matches.value.length
  } else if (event.key === 'ArrowUp' && open.value) {
    event.preventDefault()
    selected.value = (selected.value - 1 + matches.value.length) % matches.value.length
  } else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    // With no dropdown open, the vertical keys walk the sheet. Nothing in the
    // design assigns them a meaning here, and Tab alone makes an operator who
    // has just clicked a row reach for the mouse again to reach the next one.
    event.preventDefault()
    emit('row', event.key === 'ArrowUp' ? -1 : 1)
  } else if (event.key === 'Enter') {
    // A fragment matching nothing commits nothing: there is no row to take.
    if (!open.value) return
    event.preventDefault()
    emit('commit', matches.value[selected.value].tag)
    reset()
  } else if (event.key === 'Escape') {
    // Esc closes the dropdown and keeps the fragment; Esc again clears it.
    event.preventDefault()
    if (matches.value.length) clear()
    else fragment.value = ''
  } else if (event.key === 'Backspace' && fragment.value === '') {
    emit('back')
  } else if ((event.key === 'ArrowLeft' || event.key === 'ArrowRight') && !fragment.value) {
    // Chip selection moves only when there is no fragment to move a caret in.
    if (props.chips === 0) return
    event.preventDefault()
    emit('step', event.key === 'ArrowLeft' ? -1 : 1)
  } else if (event.key === 'Delete' && props.selected !== null) {
    event.preventDefault()
    emit('back')
  }
}
</script>

<template>
  <input
    v-model="fragment"
    class="fragment"
    type="text"
    :data-field="field"
    autocomplete="off"
    spellcheck="false"
    :size="Math.max(fragment.length, 1)"
    @keydown="onKey"
    @focus="$emit('focus')"
    @blur="$emit('blur')"
  />
  <TagAutocomplete
    v-if="open"
    :fragment="fragment"
    :matches="matches"
    :total="total"
    :vocabulary="vocabulary"
    :selected="selected"
    @commit="
      (tag) => {
        emit('commit', tag)
        reset()
      }
    "
  />
</template>
