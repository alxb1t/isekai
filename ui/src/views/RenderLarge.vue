<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { imageAt, photoUrl, renderDetail, thumbAt, versionOf } from '../api'
import { type PickTile, sourceGrid } from '../cells'
import ComparePick from '../components/ComparePick.vue'
import DraftDialog from '../components/DraftDialog.vue'
import KeyHint from '../components/KeyHint.vue'
import RefusalPage from '../components/RefusalPage.vue'
import { useKeys } from '../composables/useKeys'
import { plain, shifted } from '../stores/keys'
import type { RenderDetail } from '../types'

/* An image's large view (design spec J5·2): the image on `ground-media`, the
   sheet it was rendered from beside it — filled fields only, read-only. ⇧D
   drafts a flow from it, its own a revision (J5·3); ⇧C compares it with any
   image of its source, the photograph among them, picked in a grid (J5·8). */
const props = defineProps<{
  collection: string
  digest: string
  flow: string
  version: string
  seed: string
}>()
const router = useRouter()
const detail = ref<RenderDetail | null>(null)
const refusal = ref<string | null>(null)
const drafting = ref(false)
/* The pick of an image to compare with, while it is open. */
const picking = ref(false)

const place = computed(() => ({
  collection: props.collection,
  digest: props.digest,
  flow: props.flow,
  version: versionOf(props.version),
  seed: props.seed,
}))

const clock = (at: number) =>
  new Date(at * 1000).toLocaleTimeString('en-GB', { hour12: false })

const grid = computed(() => (detail.value ? sourceGrid(detail.value) : null))

/* A tile's thumbnail: the photograph's own bytes, else the render's thumbnail. */
const tileSrc = (tile: PickTile) =>
  tile === null ? photoUrl(place.value) : thumbAt({ ...place.value, ...tile })

/* Compare carries where this view was opened from, so its esc returns here
   with the same way back. */
function compare(other: PickTile): void {
  const state = { from: window.history.state?.from ?? null }
  void router.push(
    other === null
      ? { name: 'compare-photo', params: props, state }
      : {
          name: 'compare',
          params: {
            ...props,
            withFlow: other.flow,
            withVersion: `v${other.version}`,
            withSeed: other.seed,
          },
          state,
        },
  )
}

/* Where esc and the back button go: the hub when it opened this view, else
   Renders, which holds every image. A pasted address carries no state. */
const back = computed(() =>
  window.history.state?.from === 'hub'
    ? { to: { name: 'hub', params: { collection: props.collection } }, label: 'Back to Hub' }
    : { to: { name: 'renders', params: { collection: props.collection } }, label: 'Back to Renders' },
)

useKeys('screen', [
  {
    id: 'draft-from',
    keys: [shifted('KeyD')],
    label: 'draft from this',
    run: () => (drafting.value = true),
    when: () => detail.value !== null,
  },
  {
    id: 'compare',
    keys: [shifted('KeyC')],
    label: 'compare with…',
    run: () => (picking.value = true),
    when: () => grid.value !== null,
  },
  {
    id: 'back',
    keys: plain('Escape'),
    label: 'back',
    run: () => void router.push(back.value.to),
  },
])

onMounted(async () => {
  try {
    detail.value = await renderDetail(place.value)
  } catch (reason) {
    refusal.value = (reason as Error).message
  }
})
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <section v-else-if="detail" class="large">
    <div class="large__media">
      <img :src="imageAt(place)" :alt="`seed ${detail.seed}`" />
    </div>
    <aside class="large__sheet" data-sheet>
      <span class="section-label">
        {{ detail.flow }} · v{{ detail.version }} · seed {{ detail.seed }}
      </span>
      <span class="large__head mono" data-heading>
        v{{ detail.version }}<template v-if="detail.kind">
          · {{ detail.kind }} of v{{ detail.came_from }}</template
        ><template v-if="detail.approved_at !== null">
          · approved {{ clock(detail.approved_at) }}</template
        ><template v-if="detail.damaged === null">
          · count {{ detail.count }}<template v-if="detail.seeds.length">
            · seeds {{ detail.seeds.join(', ') }}</template
          ></template
        ><template v-else> · damaged</template>
      </span>
      <p v-if="detail.damaged" class="renders__refusal">
        <span class="refusal__mark" />{{ detail.damaged }}
      </p>
      <div class="large__actions">
        <div class="large__group">
          <button
            class="btn btn-secondary"
            type="button"
            data-draft-from
            @click="drafting = true"
          >
            Draft from this<KeyHint command="draft-from" />
          </button>
        </div>
        <div class="large__group">
          <button
            class="btn btn-secondary"
            type="button"
            data-compare
            @click="picking = true"
          >
            Compare with…<KeyHint command="compare" />
          </button>
        </div>
        <div class="large__group">
          <RouterLink class="btn btn-secondary" :to="back.to"
            >{{ back.label }}<KeyHint command="back" /></RouterLink
          >
        </div>
      </div>
      <dl class="large__fields">
        <template v-for="(tags, name) in detail.fields" :key="name">
          <dt class="mono">{{ name }}</dt>
          <dd>{{ tags.join(' · ') }}</dd>
        </template>
      </dl>
    </aside>
    <ComparePick
      v-if="picking && grid"
:from="detail"
      :grid="grid"
      :src="tileSrc"
      @pick="compare"
      @close="picking = false"
    />
    <DraftDialog
      v-if="drafting"
      :collection="collection"
      :images="[{ digest, flow, version: place.version, seed }]"
      :targets="detail.targets"
      @close="drafting = false"
    />
  </section>
</template>
