<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { comparison, imageAt } from '../api'
import KeyBar from '../components/KeyBar.vue'
import RefusalPage from '../components/RefusalPage.vue'
import { useKeys } from '../composables/useKeys'
import { plain } from '../stores/keys'
import type { CompareSide, Comparison } from '../types'

/* Before and after (design spec J5·9): one seed under the newest older version
   and under this one, at equal size, with what changed between their sheets.
   Same seed, same composition: the difference left is the edit. `\` swaps the
   sides in place; esc goes back to the large view. */
const props = defineProps<{
  batch: string
  digest: string
  flow: string
  version: string
  seed: string
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

const image = (side: CompareSide) =>
  imageAt({ ...props, version: side.version, seed: props.seed })

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
        params: { ...props },
        state: { from: window.history.state?.from ?? null },
      }),
  },
])

onMounted(async () => {
  try {
    pair.value = await comparison({
      ...props,
      version: Number(props.version.replace(/^v/, '')),
    })
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
        <img :src="image(side)" :alt="`${label} v${side.version} seed ${pair.seed}`" />
        <span class="compare__line mono">{{ seeds(side) }} · {{ side.tokens }} tokens</span>
      </figure>
    </div>
    <div class="compare__change mono" data-changed>
      <span>same seed · {{ pair.seed }}</span>
      <span class="section-label">
        {{ pair.changed.length }} field{{ pair.changed.length === 1 ? '' : 's' }} changed
      </span>
      <span v-for="one in pair.changed" :key="one.field" class="compare__field">
        {{ one.field }} {{ one.before.join(' · ') || 'empty' }} →
        {{ one.after.join(' · ') || 'empty' }}
      </span>
    </div>
    <KeyBar />
  </section>
</template>
