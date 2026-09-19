<script setup lang="ts">
import type { Budget } from '../types'
import TokenBudget from './TokenBudget.vue'

/* The kicker states which of stage ③'s three readings this is, and the line
   below it counts the fields. Frame delta 5: the design's `none marked
   intentional` goes with the empties gate -- an empty field is legal and
   nothing insists on a claim, so nothing counts unclaimed ones either. */
defineProps<{
  kicker: string
  fields: number
  filled: number
  budget: Budget | null
}>()
</script>

<template>
  <header class="sheet-header">
    <div>
      <span class="kicker">③ sheet — {{ kicker }}</span>
      <p class="sheet-header__line">
        {{ fields }} fields, schema order. {{ filled }} filled ·
        {{ fields - filled }} empty.
      </p>
    </div>
    <TokenBudget :budget="budget" />
  </header>
</template>
