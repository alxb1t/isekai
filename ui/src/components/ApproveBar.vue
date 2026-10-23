<script setup lang="ts">
import { ref } from 'vue'
import KeyHint from './KeyHint.vue'

/* Approve, or the fact that it happened, and every refusal the page meets.

   **Accent-outlined and always live.** No scroll gate, no dwell timer, no
   confirmation step, and no disabled twin: the only thing that stops an approve
   is a refusal, never a ritual. Once approved the button becomes a stated time
   rather than a greyed-out copy of itself.

   Discard, on a revision, sits left of Approve and asks before it deletes: it
   takes the operator's edits with the draft. Review keys this bar by sheet, so
   an ask never outlives its sheet. */
defineProps<{
  approved: boolean
  at: string | null
  working: boolean
  /* The page's refusal, verbatim; the work it names is never lost. */
  refusal?: string | null
  discardable?: boolean
}>()

const emit = defineEmits<{ approve: []; discard: [] }>()
const asking = ref(false)

function discard(): void {
  asking.value = false
  emit('discard')
}
</script>

<template>
  <footer class="approve-bar">
    <p v-if="refusal" class="approve-bar__refusal mono">
      <span class="refusal__mark" />{{ refusal }}
    </p>
    <template v-if="approved">
      <span class="approve-bar__note mono">This sheet is approved and read-only.</span>
      <span class="approve-bar__fact">
        <span class="approve-bar__dot" />
        <span class="mono">Approved {{ at }}</span>
      </span>
    </template>
    <template v-else>
      <span class="approve-bar__note">Saving happens on its own.</span>
      <span v-if="asking" class="approve-bar__ask" data-discard-confirm>
        Delete this draft and its edits?
        <button class="btn btn-secondary" type="button" @click="asking = false">Keep</button>
        <button class="btn btn-secondary" type="button" @click="discard">Delete</button>
      </span>
      <button
        v-else-if="discardable"
        class="btn btn-secondary"
        type="button"
        data-discard
        @click="asking = true"
      >
        Discard draft
      </button>
      <button
        class="btn btn-primary"
        type="button"
        :disabled="working"
        @click="$emit('approve')"
      >
        Approve sheet<KeyHint command="approve" />
      </button>
    </template>
  </footer>
</template>
