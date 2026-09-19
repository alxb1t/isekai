<script setup lang="ts">
/* The photograph, through the system's `.lighten` wrapper so dark values fall
   away into the page. The overlay is the one place that blend is not applied. */
defineProps<{ src: string; alt: string; loading?: boolean; ratio: string }>()
defineEmits<{ open: [] }>()
</script>

<template>
  <button class="photo-frame" type="button" @click="$emit('open')">
    <div
      v-if="loading"
      class="rail__placeholder"
      :style="{ aspectRatio: ratio, width: '100%' }"
    />
    <div v-else class="lighten"><img :src="src" :alt="alt" /></div>
  </button>
</template>
