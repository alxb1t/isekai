<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { comparison, imageAt, versionOf } from '../api'
import RefusalPage from '../components/RefusalPage.vue'
import { useKeys } from '../composables/useKeys'
import { plain } from '../stores/keys'
import type { CompareSide, Comparison } from '../types'

/* Before and after (design spec J5·9): this image beside another of its cell —
   the one picked, else its seed under the newest older version — at equal size,
   the older of the two before as the server orders them, with what changed between their sheets, saying when the seeds differ or the
   sheets are the same. Same seed, same composition: the difference left is the
   edit. `\` swaps the sides in place; esc goes back to the large view. */
const props = defineProps<{
  collection: string
  digest: string
  flow: string
  version: string
  seed: string
  with?: string
  withSeed?: string
}>()
const router = useRouter()
const pair = ref<Comparison | null>(null)
const refusal = ref<string | null>(null)
const swapped = ref(false)

const sides = computed<[string, CompareSide][]>(() => {
  const held = pair.value
  if (!held) return []
  const both: [string, CompareSide][] = [
    ['before', held.before],
    ['after', held.after],
  ]
  return swapped.value ? both.reverse() : both
})

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

const image = (side: CompareSide) =>
  imageAt({ ...large.value, version: side.version, seed: side.seed })

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
      props.with && props.withSeed
        ? { version: versionOf(props.with), seed: props.withSeed }
        : undefined
    pair.value = await comparison({ ...large.value, version: versionOf(props.version) }, other)
  } catch (reason) {
    refusal.value = (reason as Error).message
  }
})
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <section v-else-if="pair" class="compare" data-compare-view>
    <div class="compare__sides">
      <figure v-for="[label, side] in sides" :key="label" class="compare__side" :data-side="label">
        <figcaption class="section-label">
          {{ label }} · v{{ side.version }} · approved {{ clock(side.approved_at) }}
        </figcaption>
        <img :src="image(side)" :alt="`${label} v${side.version} seed ${side.seed}`" />
        <span class="compare__line mono">{{ seeds(side) }} · {{ side.tokens }} tokens</span>
      </figure>
    </div>
    <div class="compare__change mono" data-changed>
      <span v-if="pair.different_seeds" data-seeds-differ
        >different seeds · {{ pair.before.seed }} → {{ pair.after.seed }}</span
      >
      <span v-else>same seed · {{ pair.after.seed }}</span>
      <span v-if="pair.same_sheet" data-same-sheet>same sheet</span>
      <span class="section-label">
        {{ pair.changed.length }} field{{ pair.changed.length === 1 ? '' : 's' }} changed
      </span>
      <span v-for="one in pair.changed" :key="one.field" class="compare__field">
        {{ one.field }} {{ one.before.join(' · ') || 'empty' }} →
        {{ one.after.join(' · ') || 'empty' }}
      </span>
    </div>
  </section>
</template>
