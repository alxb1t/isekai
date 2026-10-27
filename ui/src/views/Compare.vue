<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { comparison, imageAt, photoUrl, versionOf } from '../api'
import RefusalPage from '../components/RefusalPage.vue'
import { useKeys } from '../composables/useKeys'
import { plain } from '../stores/keys'
import type { CompareSide, Comparison } from '../types'

/* Compare (design spec J5·9): the image picked on the left, the one compare
   started from on the right, at one height, each headed by its flow, version
   and seed. Between two renders, the fields both flows declare that differ,
   saying when the seeds differ or the sheets are the same; with the
   photograph, the pair alone. `\` swaps the sides in place; esc goes back to
   the large view. */
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

/* The pair of two renders, or null beside the photograph. */
const renders = computed(() => (pair.value && 'changed' in pair.value ? pair.value : null))

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

/* Each side's aspect ratio once it loads: widths in proportion put both at one height. */
const ratios = ref<Record<string, number>>({ left: 1, right: 1 })

function loaded(label: string, event: Event): void {
  const held = event.target as HTMLImageElement
  if (held.naturalHeight) ratios.value[label] = held.naturalWidth / held.naturalHeight
}

/* As wide as the screen allows, and no taller than it. */
const width = computed(
  () => `min(100%, calc((100vh - 200px) * ${ratios.value.left + ratios.value.right}))`,
)

const clock = (at: number | null) =>
  at === null ? '' : new Date(at * 1000).toLocaleTimeString('en-GB', { hour12: false })

const seeds = (side: CompareSide) =>
  `count ${side.renders.count}${side.renders.seeds.length ? ` · seeds ${side.renders.seeds.join(', ')}` : ''}`

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

const named = (side: CompareSide | null) =>
  side === null ? 'photograph' : `${side.flow} · v${side.version} · seed ${side.seed}`

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
        :style="{ flexGrow: ratios[label] }"
        :data-side="label"
      >
        <figcaption class="section-label">
          {{ named(side) }}<template v-if="side"> · approved {{ clock(side.approved_at) }}</template>
        </figcaption>
        <img :src="image(side)" :alt="named(side)" @load="loaded(label, $event)" />
        <span v-if="side" class="compare__line mono">{{ seeds(side) }} · {{ side.tokens }} tokens</span>
      </figure>
    </div>
    <div v-if="renders" class="compare__change mono" data-changed>
      <span v-if="renders.different_seeds" data-seeds-differ
        >different seeds · {{ renders.left.seed }} · {{ renders.right.seed }}</span
      >
      <span v-else>same seed · {{ renders.right.seed }}</span>
      <span v-if="renders.same_sheet" data-same-sheet>same sheet</span>
      <span class="section-label">
        {{ renders.changed.length }} field{{ renders.changed.length === 1 ? '' : 's' }} differ{{
          renders.changed.length === 1 ? 's' : ''
        }}
      </span>
      <span v-for="one in renders.changed" :key="one.field" class="compare__field" data-field>
        {{ one.field }} {{ one.left.join(' · ') || 'empty' }} │
        {{ one.right.join(' · ') || 'empty' }}
      </span>
    </div>
  </section>
</template>
