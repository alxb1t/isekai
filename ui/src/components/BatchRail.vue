<script setup lang="ts">
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
  return props.edited.has(input.id) ? 'half' : 'hollow'
}

const approved = () => props.inputs.filter((i) => i.status === 'approved').length
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
          v-if="loading"
          class="rail__placeholder"
          :style="{ aspectRatio: `${input.width} / ${input.height}` }"
        />
        <div v-else class="lighten">
          <img class="rail__thumb" :src="photoUrl(input.id)" :alt="input.id" />
        </div>
        <span class="rail__foot mono">
          <span>{{ input.id.split('_').slice(1).join('_') || input.id }}</span>
          <StatusMark :kind="mark(input)" :size="8" rail />
        </span>
      </button>
    </div>

    <div class="rail__legend">
      <span class="rail__legend-row"><StatusMark kind="filled" :size="8" rail /> approved</span>
      <span class="rail__legend-row"><StatusMark kind="half" :size="8" /> edited</span>
      <span class="rail__legend-row"><StatusMark kind="hollow" :size="8" /> untouched</span>
    </div>

    <!-- The only route to the manifest mid-batch, clickable at any time. -->
    <button class="rail__run mono" type="button" @click="$emit('manifest')">
      run · {{ approved() }} of {{ inputs.length }} approved
    </button>
  </nav>
</template>
