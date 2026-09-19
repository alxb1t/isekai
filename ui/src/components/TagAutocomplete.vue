<script setup lang="ts">
import type { VocabEntry } from '../types'

/* The dropdown.

   **It overlays and never displaces.** Absolutely positioned at `top: 30px`
   under its row: if the rows below it moved, the operator would lose their place
   mid-word, and they are typing with their eyes on the photograph.

   Row 1 is preselected, so the highest post count is one ⏎ away and reaching a
   rare tag takes a deliberate ↓. Counts are mono and tabular because they are
   read by digit count -- `1,204,331` against `903` is a shape difference rather
   than a reading task, and that only works if the digits align.

   Frame delta 10: 2a and 2b are layout and behaviour references, never content
   ones. Their rows are not reproducible against the real prediction set --
   `blonde` returns two tags here, not four. */
defineProps<{
  matches: VocabEntry[]
  total: number
  vocabulary: number
  selected: number
}>()

defineEmits<{ commit: [tag: string] }>()

const grouped = (posts: number) => posts.toLocaleString('en-GB')
</script>

<template>
  <div v-if="matches.length" class="drop">
    <button
      v-for="(match, index) in matches"
      :key="match.tag"
      class="drop__row"
      :class="{ 'drop__row--selected': index === selected }"
      type="button"
      tabindex="-1"
      @mousedown.prevent="$emit('commit', match.tag)"
    >
      <span class="drop__tag">{{ match.tag }}</span>
      <span class="drop__posts mono">
        {{ grouped(match.posts) }}<span v-if="match.rare" class="drop__rare"> · rare</span>
      </span>
    </button>
    <div class="drop__foot mono">
      <span>↑↓ move · ⏎ commit · esc close</span>
      <span>{{ grouped(total) }} of {{ grouped(vocabulary) }}</span>
    </div>
  </div>
</template>
