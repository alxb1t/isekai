<script setup lang="ts">
/* Counted, not spun.

   A local read finishes in a moment, and **if it does not, the operator wants to
   know which file it is stuck on** — so this names what is being read rather
   than turning. It names the input rather than counting `2 of 3`: the browser
   reads one input at a time, so a count would be `1 of 3` forever, while the
   file's own name is the thing the stated reason asks for.

   Flat bars and no shimmer elsewhere: an animated skeleton pulls the eye off the
   photograph, which is the one thing on screen worth looking at. */
defineProps<{ reading: string | null; vocabulary: number }>()
</script>

<template>
  <p class="skeleton__line mono">
    <span v-if="reading">reading {{ reading }}…</span>
    <span v-else>reading the batch…</span>
    <template v-if="vocabulary">
      · vocabulary {{ vocabulary.toLocaleString('en-GB') }} tags · loaded
    </template>
  </p>
</template>
