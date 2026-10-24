<script setup lang="ts">
import { reasons } from '../bars'
import KeyHint from './KeyHint.vue'
import { storeToRefs } from 'pinia'
import { useLiveStore } from '../stores/live'
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

const live = useLiveStore()
const { job } = storeToRefs(live)
const { renderTotals } = live
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
        Render<KeyHint command="render" />
      </button>
    </template>
    <template v-else>
      <span class="prepare-bar__cells mono">{{ renderTotals(job) }}</span>
      <RouterLink
        v-if="job?.session"
        class="btn btn-secondary"
        :to="{ name: 'session', params: { batch: job.batch, id: job.session.id } }"
        >Session<KeyHint command="session" /></RouterLink
      >
    </template>
  </div>
</template>
