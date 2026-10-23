<script setup lang="ts">
import type { Budget } from '../types'
import TokenBudget from './TokenBudget.vue'

/* The kicker states which of stage ③'s readings this is, and its receipt: the
   draft's save, or the approval's time inside `kicker`. No path, no count. */
defineProps<{
  kicker: string
  budget: Budget | null
  saving?: boolean
  saved?: string | null
}>()
</script>

<template>
  <header class="sheet-header">
    <span class="kicker"
      >③ sheet — {{ kicker
      }}<!-- Fixed width, so the kicker does not shift when the spinner gives way
           to the time it was waiting for. --><span
        v-if="saving || saved"
        class="receipt__when"
      >
        <span v-if="saving" class="spinner" aria-label="saving" />
        <template v-else>· saved {{ saved }}</template>
      </span></span
    >
    <TokenBudget :budget="budget" />
  </header>
</template>
