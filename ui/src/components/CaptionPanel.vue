<script setup lang="ts">
import { computed } from 'vue'

/* All paragraphs, expanded.

   Frame delta 4: no tinted phrases and no dashed runs. The design lit the phrase
   a field was mapped from, but `sheet.py` discards the phrases -- the sorter is
   asked for tags, not for spans -- and the briefing forbids substring
   provenance, so there is nothing on disk to light. Drawing it would mean
   inventing the mapping in the browser. */
const props = defineProps<{ prose: string | null; loading?: boolean }>()

const paragraphs = computed(() =>
  (props.prose ?? '').split(/\n{2,}/).map((p) => p.trim()).filter(Boolean),
)

const words = computed(() => (props.prose ?? '').split(/\s+/).filter(Boolean).length)
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
      <p v-for="(paragraph, index) in paragraphs" v-else :key="index">{{ paragraph }}</p>
    </div>
  </section>
</template>
