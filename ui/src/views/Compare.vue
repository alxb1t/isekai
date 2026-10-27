<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { comparison, imageAt, photoUrl, versionOf } from '../api'
import { imageName } from '../cells'
import RefusalPage from '../components/RefusalPage.vue'
import { useKeys } from '../composables/useKeys'
import { usePair } from '../composables/usePair'
import { plain } from '../stores/keys'
import type { CompareSide, Comparison } from '../types'

/* Compare (design spec J5·9): the image picked on the left, the one compare
   started from on the right, at one height, each headed by its flow, version
   and seed alone, so the images take the room. `\` swaps the sides in place;
   esc goes back to the large view. */
const props = defineProps<{
  collection: string
  digest: string
  flow: string
  version: string
  seed: string
  withFlow?: string
  withVersion?: string
  withSeed?: string
}>()
const router = useRouter()
const pair = ref<Comparison | null>(null)
const refusal = ref<string | null>(null)
const swapped = ref(false)

/* A side is a render, or the photograph where it is null. */
const sides = computed<[string, CompareSide | null][]>(() => {
  const held = pair.value
  if (!held) return []
  const both: [string, CompareSide | null][] = [
    ['left', held.left],
    ['right', held.right],
  ]
  return swapped.value ? both.reverse() : both
})

/* The pair, as wide as the screen allows and as tall as it less the app bar, the
   page's padding and the heads; a ratio stays with its side when `\` swaps them. */
const { ratios, loaded, width } = usePair([1, 1], '100%', '(100vh - 88px)')
const at = (label: string) => (label === 'left' ? 0 : 1)

/* The large view this was opened from: its address without the other image. */
const large = computed(() => ({
  collection: props.collection,
  digest: props.digest,
  flow: props.flow,
  version: props.version,
  seed: props.seed,
}))

const image = (side: CompareSide | null) =>
  side === null
    ? photoUrl(large.value)
    : imageAt({ ...large.value, flow: side.flow, version: side.version, seed: side.seed })

useKeys('screen', [
  {
    id: 'swap',
    keys: plain('Backslash'),
    label: 'swap in place',
    run: () => (swapped.value = !swapped.value),
  },
  {
    id: 'back',
    keys: plain('Escape'),
    label: 'back',
    // Back to the large view, with the way back it was opened with.
    run: () =>
      void router.push({
        name: 'render',
        params: large.value,
        state: { from: window.history.state?.from ?? null },
      }),
  },
])

onMounted(async () => {
  try {
    const other =
      props.withFlow && props.withVersion && props.withSeed
        ? { flow: props.withFlow, version: versionOf(props.withVersion), seed: props.withSeed }
        : null
    pair.value = await comparison({ ...large.value, version: versionOf(props.version) }, other)
  } catch (reason) {
    refusal.value = (reason as Error).message
  }
})
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <section v-else-if="pair" class="compare" data-compare-view>
    <div class="compare__sides" :style="{ width }">
      <figure
        v-for="[label, side] in sides"
        :key="label"
        class="compare__side"
        :style="{ flexGrow: ratios[at(label)] }"
        :data-side="label"
      >
        <figcaption class="section-label">{{ imageName(side) }}</figcaption>
        <img :src="image(side)" :alt="imageName(side)" @load="loaded(at(label), $event)" />
      </figure>
    </div>
  </section>
</template>
