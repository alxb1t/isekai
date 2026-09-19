<script setup lang="ts">
import { computed } from 'vue'
import { ENCODER_WINDOW, type Budget } from '../types'

/* The total, the bar, and where the weight sits.

   Frame delta 8. The design drew `30 / 77`, because it counted the sheet's words
   alone; `token_budget()` counts the assembled prompt, so the flow's prefix and
   trailer are in the number and every real sheet clears 77. Over budget is
   therefore the normal reading, and it is styled as information: the bar clamps
   at 100% and the total takes the accent. Nothing else of the over-budget frame
   is built -- no split bar, no hairline, no `27 over` chip, no footer advice.

   The rows sum into the total and `overhead` is the remainder, so `heaviest`
   reconciles with the per-row column instead of disagreeing with it. */
const props = defineProps<{ budget: Budget | null }>()

const over = computed(() => (props.budget?.total ?? 0) > ENCODER_WINDOW)

const width = computed(() => {
  if (!props.budget) return 0
  return Math.min(100, (props.budget.total / ENCODER_WINDOW) * 100)
})

const heaviest = computed(() => {
  if (!props.budget) return ''
  return Object.entries(props.budget.per_field)
    .filter(([, tokens]) => tokens > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([name, tokens]) => `${name} ${tokens}`)
    .join(' · ')
})
</script>

<template>
  <div class="budget">
    <span class="budget__total mono" :class="{ 'budget__total--over': over }">
      {{ budget ? budget.total : '—' }}
    </span>
    <span class="budget__window mono"> / {{ ENCODER_WINDOW }} tokens</span>
    <div class="budget__bar">
      <div
        class="budget__fill"
        :class="{ 'budget__fill--over': over }"
        :style="{ width: `${width}%` }"
      />
    </div>
    <div v-if="heaviest" class="budget__heaviest mono">heaviest: {{ heaviest }}</div>
  </div>
</template>
