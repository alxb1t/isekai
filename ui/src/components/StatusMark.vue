<script setup lang="ts">
import type { MarkKind } from '../types'

/* The whole shape system, one component. Status is shape-coded rather than
   colour-coded, because the system has one accent and no error colour -- so a
   mark survives a mono palette where a tint would not. The square is the one
   kind that is gone: it meant "refusal on this field" and went with the
   refusal surface. `reopened` is a ring rather than a disc, because a
   re-opened input has been approved and is open again -- neither state alone. */
withDefaults(defineProps<{ kind: MarkKind; size?: number; rail?: boolean }>(), {
  size: 7,
  rail: false,
})
</script>

<template>
  <span
    class="mark"
    :class="[`mark--${kind}`, { 'mark--rail-filled': rail && kind === 'filled' }]"
    :style="{ width: `${size}px`, height: `${size}px` }"
  />
</template>
