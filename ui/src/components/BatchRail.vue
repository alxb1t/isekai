<script setup lang="ts">
import { ref } from 'vue'
import type { BatchInput, MarkKind } from '../types'
import StatusMark from './StatusMark.vue'

/* Thumbnails at their true aspect ratio: orientation is part of how the
   operator recognises an input, so a square crop would take that away. */
const props = defineProps<{
  inputs: BatchInput[]
  current: string
  edited: Set<string>
  photoUrl: (id: string) => string
  loading?: boolean
}>()

defineEmits<{ select: [id: string]; manifest: [] }>()

function mark(input: BatchInput): MarkKind {
  if (props.loading) return 'dashed'
  if (input.status === 'approved') return 'filled'
  if (input.status === 're-opened') return 'reopened'
  return props.edited.has(input.id) ? 'half' : 'hollow'
}

/* Counts what the run directories hold, which is what `/api/batch`'s own
   `approved` reports -- a re-opened input still has an approved artifact, so
   excluding it here would make the rail disagree with the header. */
const approved = () => props.inputs.filter((i) => i.status !== 'draft').length

/* Same rule as the hero: a thumbnail appears whole or not at all, so the rail
   never shows a photograph half-decoded and never reflows as one arrives. */
const decoded = ref(new Set<string>())

function ready(id: string): void {
  if (decoded.value.has(id)) return
  decoded.value = new Set(decoded.value).add(id)
}
</script>

<template>
  <nav class="rail">
    <span class="kicker">batch</span>
    <div class="rail__cards">
      <button
        v-for="input in inputs"
        :key="input.id"
        class="rail__card"
        :class="{ 'rail__card--current': input.id === current }"
        type="button"
        @click="$emit('select', input.id)"
      >
        <div
          v-show="loading || !decoded.has(input.id)"
          class="rail__placeholder"
          :style="{ aspectRatio: `${input.width} / ${input.height}` }"
        />
        <div v-show="!loading && decoded.has(input.id)" class="lighten">
          <img
            class="rail__thumb"
            :src="photoUrl(input.id)"
            :alt="input.id"
            @load="ready(input.id)"
          />
        </div>
        <span class="rail__foot mono">
          <span>{{ input.id.split('_').slice(1).join('_') || input.id }}</span>
          <StatusMark :kind="mark(input)" :size="8" rail />
        </span>
      </button>
    </div>

    <div class="rail__legend">
      <span class="rail__legend-row"><StatusMark kind="filled" :size="8" rail /> approved</span>
      <span class="rail__legend-row"><StatusMark kind="reopened" :size="8" /> re-opened</span>
      <span class="rail__legend-row"><StatusMark kind="half" :size="8" /> edited</span>
      <span class="rail__legend-row"><StatusMark kind="hollow" :size="8" /> untouched</span>
    </div>

    <!-- The only route to the manifest mid-batch, clickable at any time. -->
    <button class="rail__run mono" type="button" @click="$emit('manifest')">
      run · {{ approved() }} of {{ inputs.length }} approved
    </button>
  </nav>
</template>
