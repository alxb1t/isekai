<script setup lang="ts">
import { computed } from 'vue'
import { sentencesOf, wordsOf } from '../caption'

/* The whole caption, expanded, one sentence to a block.

   Frame delta 4: no tinted phrases and no dashed runs. The design lit the phrase
   a field was mapped from, but `sheet.py` discards the phrases -- the sorter is
   asked for tags, not for spans -- and the briefing forbids substring
   provenance, so there is nothing on disk to light. Drawing it would mean
   inventing the mapping in the browser.

   v0.20 delta: the block boundary moves from the paragraph to the sentence, and
   nothing else about this panel changes. No new component, colour, spacing or
   type step (design.md D21). */
const props = defineProps<{ prose: string | null; loading?: boolean }>()

/* One sentence to a block, not one paragraph. Reading a caption to correct a
   sheet is not reading it for sense: the operator looks for one attribute at a
   time, loses his place mid-paragraph, and re-reads. A block per sentence gives
   the eye a place to return to, and it is the whole of ④ -- the sentence labels
   the design once carried were measured against real captions and refused
   (design.md D2). */
const sentences = computed(() => sentencesOf(props.prose))

const words = computed(() => wordsOf(props.prose))
</script>

<template>
  <section class="caption">
    <div class="source__head">
      <span class="kicker">② caption</span>
      <span class="source__meta mono">{{ loading ? 'reading…' : `${words} words` }}</span>
    </div>
    <div class="caption__body">
      <template v-if="loading">
        <div
          v-for="n in 4"
          :key="n"
          style="height: 9px; margin-bottom: 10px; background: var(--color-neutral-900)"
        />
        <span class="mono" style="font-size: 11px; color: var(--color-neutral-500)">
          reading…
        </span>
      </template>
      <p v-for="(sentence, index) in sentences" v-else :key="index">{{ sentence }}</p>
    </div>
  </section>
</template>
