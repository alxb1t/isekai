<script setup lang="ts">
import { ref, watch } from 'vue'

/* The photograph, through the system's `.lighten` wrapper so dark values fall
   away into the page. The overlay is the one place that blend is not applied.

   **Nothing is shown until it has decoded.** A striped placeholder holds the
   frame at the photograph's own aspect ratio until the bytes are there, because
   half a photo is worse than none when the job is judging one -- and because a
   frame that grows into place reflows the column under the operator's eyes. */
const props = defineProps<{ src: string; alt: string; loading?: boolean; ratio: string }>()
defineEmits<{ open: [] }>()

const ready = ref(false)

watch(
  () => props.src,
  () => {
    ready.value = false
  },
)
</script>

<template>
  <button class="photo-frame" type="button" @click="$emit('open')">
    <div
      v-show="loading || !ready"
      class="rail__placeholder"
      :style="{ aspectRatio: ratio, width: '100%' }"
    />
    <div v-show="!loading && ready" class="lighten">
      <img :src="src" :alt="alt" @load="ready = true" />
    </div>
  </button>
</template>
