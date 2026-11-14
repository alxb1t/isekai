<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { type Place, inkView, photoUrl, tattooNamed } from '../api'
import { thumbCrop } from '../tattoos'
import type { Outline, Tattoo } from '../types'

/* A cut's card image: the photograph cropped to the outline's box, and once the outline is
   closed the ink view the server draws for it. With no box, or a read that fails, the whole
   photograph stands as before. */
const props = defineProps<{ place: Place; tattoo: Tattoo }>()

const outline = ref<Outline | null>(null)
const ink = ref<string | null>(null)

const crop = computed(() => (outline.value ? thumbCrop(outline.value.points, props.tattoo.size) : null))
const style = computed(() =>
  crop.value
    ? {
        width: `${crop.value.width}px`,
        height: `${crop.value.height}px`,
        backgroundImage: `url(${photoUrl(props.place)})`,
        backgroundSize: crop.value.backgroundSize,
        backgroundPosition: crop.value.backgroundPosition,
      }
    : null,
)

onMounted(async () => {
  try {
    const held = await tattooNamed(props.place.digest, props.tattoo.name)
    outline.value = held.outline
    if (!held.outline.closed) return
    const made = await inkView(props.place.collection, props.tattoo.name, held.outline, props.place)
    ink.value = URL.createObjectURL(made.image)
  } catch {
    // The card keeps what it shows: the crop, or the whole photograph.
  }
})

onUnmounted(() => {
  if (ink.value) URL.revokeObjectURL(ink.value)
})
</script>

<template>
  <img v-if="ink" class="picker__image" :src="ink" :alt="tattoo.name" />
  <div v-else-if="style" class="picker__crop" :style="style" role="img" :aria-label="tattoo.name" />
  <img v-else class="picker__image" :src="photoUrl(place)" :alt="tattoo.name" loading="lazy" />
</template>
