<script setup lang="ts">
/* Approve, or the fact that it happened.

   **Accent-outlined and always live.** No scroll gate, no dwell timer, no
   confirmation step, and no disabled twin: the only thing that stops an approve
   is a refusal, never a ritual. Frame delta 5 takes the empties action with it --
   a control that marked something nothing reads would be a control with no
   consequence.

   Once approved the button becomes a stated time rather than a greyed-out copy
   of itself, and the footer states that the input is read-only and names the
   file that holds it (frame deltas 6 and 7, Design D5). There is no exit
   affordance, because there is nothing on disk for an edit after approval to be
   written into: `approve()` deletes the draft, and opening the surface again
   writes no replacement. */
defineProps<{
  approved: boolean
  at: string | null
  file: string | null
  working: boolean
}>()

defineEmits<{ approve: [] }>()
</script>

<template>
  <footer class="approve-bar">
    <span v-if="approved" class="approve-bar__note mono">
      This input is approved and read-only. It is
      <span class="app-header__receipt--approved">{{ file }}</span
      >; a new version is an explicit act, taken from the terminal.
    </span>
    <span v-else class="approve-bar__note">Saving happens on its own.</span>

    <span v-if="approved" class="approve-bar__fact">
      <span class="approve-bar__dot" />
      <span class="mono">Approved {{ at }}</span>
    </span>
    <button
      v-else
      class="btn btn-primary"
      type="button"
      :disabled="working"
      @click="$emit('approve')"
    >
      Approve sheet <span class="mono">⌘↩</span>
    </button>
  </footer>
</template>
