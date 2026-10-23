<script setup lang="ts">
import { reasons } from '../bars'
import { useLive } from '../composables/useLive'
import { noun } from '../words'

/* The Render bar (design spec J2): the images short of their count, with Render,
   or, with none short, the running session's totals and the way to it. Its
   button keeps `data-render`; a disabled one has its reason beside it. A count
   the render stage refuses keeps Render, disabled, so the reason is never silent.
   `rendering` is a session running for this bar's own batch. */
defineProps<{
  images: number
  disabled: string | null
  refused: string | null
  rendering: boolean
}>()
defineEmits<{ open: [] }>()

const { job, renderTotals } = useLive()
</script>

<template>
  <div class="prepare-bar" :class="{ running: rendering }" data-render-bar>
    <template v-if="images > 0 || (refused !== null && !rendering)">
      <span v-if="images > 0" class="prepare-bar__cells mono">
        {{ images }} {{ noun(images, 'image') }} ready to render
      </span>
      <span
        v-for="reason in reasons(disabled, refused)"
        :key="reason"
        class="hub__reason"
        data-render-reason
        >{{ reason }}</span
      >
      <button
        class="btn btn-primary"
        type="button"
        data-render
        :disabled="disabled !== null"
        @click="$emit('open')"
      >
        Render<span class="appbar__key">⌥R</span>
      </button>
    </template>
    <template v-else>
      <span class="prepare-bar__cells mono">{{ renderTotals(job) }}</span>
      <RouterLink class="btn btn-secondary" :to="{ name: 'session' }"
        >Session<span class="appbar__key">⌥4</span></RouterLink
      >
    </template>
  </div>
</template>
