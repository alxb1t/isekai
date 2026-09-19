<script setup lang="ts">
import StatusMark from './StatusMark.vue'

/* The run line and the receipts.

   Two frame deltas live here. The `Show ② draft` pill is cut, because its ON
   state is never drawn anywhere in the design and a control with no drawn
   consequence is worse than an absent one. And the run line loses its date: a
   run id is `<12 hex>_<slug>` and carries none, so it reads
   `summon-v1 · 3 inputs · 0 approved` instead of `run 2026-09-17 · …`. */
defineProps<{
  flow: string
  inputs: number
  approved: number
  draft: string | null
  saved: string | null
  approvedName: string | null
  approvedAt: string | null
  refusal: string | null
}>()

defineSlots<{ status?: () => unknown }>()
</script>

<template>
  <div>
    <header class="app-header">
      <span class="app-header__brand">isekai review</span>
      <span class="app-header__run mono">
        {{ flow }} · {{ inputs }} inputs · {{ approved }} approved
      </span>
      <slot name="status" />
      <div class="app-header__receipts mono">
        <span v-if="draft">{{ draft }}<template v-if="saved"> · saved {{ saved }}</template></span>
        <span v-if="approvedName" class="app-header__receipt--approved">
          {{ approvedName }}<template v-if="approvedAt"> · approved {{ approvedAt }}</template>
        </span>
      </div>
    </header>
    <!-- The one place a Refusal lands. There is no queue and no modal; the
         string is carried verbatim, and nothing here implies work was lost. -->
    <p v-if="refusal" class="app-header__refusal mono">
      <StatusMark kind="hollow" :size="7" /> refused: {{ refusal }}
    </p>
  </div>
</template>
