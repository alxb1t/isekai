<script setup lang="ts">
import { computed } from 'vue'
import CaptionPanel from './CaptionPanel.vue'
import PhotoFrame from './PhotoFrame.vue'

/* Owns the 492/620px width rule: one rule, two shapes, no second layout. The
   photo always fills its column's width and the form column absorbs the
   difference, so a wide photograph never letterboxes. */
const props = defineProps<{
  id: string
  width: number
  height: number
  photo: string
  caption: string | null
  loading?: boolean
}>()

defineEmits<{ open: [] }>()

const landscape = computed(() => props.width > props.height)
</script>

<template>
  <aside class="source" :class="landscape ? 'source--landscape' : 'source--portrait'">
    <div class="source__head">
      <span class="kicker">① photograph</span>
      <span class="source__meta mono">
        {{ id }} · {{ width }}×{{ height }} ·
        {{ loading ? 'reading…' : 'click to fill window' }}
      </span>
    </div>
    <PhotoFrame
      :src="photo"
      :alt="id"
      :loading="loading"
      :ratio="`${width} / ${height}`"
      @open="$emit('open')"
    />
    <CaptionPanel :prose="caption" :loading="loading" />
  </aside>
</template>
