<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { imageAt, photoUrl, renderDetail, versionOf } from '../api'
import { type CellImage, others as othersOf, pick } from '../cells'
import ComparePick from '../components/ComparePick.vue'
import DraftDialog from '../components/DraftDialog.vue'
import ImageViewer from '../components/ImageViewer.vue'
import KeyHint from '../components/KeyHint.vue'
import RefusalPage from '../components/RefusalPage.vue'
import { useKeys } from '../composables/useKeys'
import { plain, shifted } from '../stores/keys'
import type { RenderDetail } from '../types'

/* An image's large view (design spec J5·2): the image on `ground-media`, the
   sheet it was rendered from beside it — filled fields only, read-only. ⇧D
   drafts a flow from it, its own a revision (J5·3); c compares it with another
   image of its cell, picked in a dialog of tiles (J5·8); ⇧C sets it beside its
   run's photograph. */
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
/* The image beside its run's photograph, in the viewer's pair. */
const pairing = ref(false)
/* The tile the dialog picking the image to compare with opens on, while it is open. */
const picking = ref<number | null>(null)
const pair = computed(() => [
  { src: photoUrl(place.value), name: 'photograph' },
  { src: imageAt(place.value), name: `seed ${props.seed}` },
])

const place = computed(() => ({
  collection: props.collection,
  digest: props.digest,
  flow: props.flow,
  version: versionOf(props.version),
  seed: props.seed,
}))

const clock = (at: number) =>
  new Date(at * 1000).toLocaleTimeString('en-GB', { hour12: false })

/* The cell's other images, in the order Renders draws them. */
const others = computed(() =>
  othersOf(detail.value?.images ?? [], place.value.version, props.seed),
)
const choices = computed(() =>
  others.value.map((one) => ({ ...one, src: imageAt({ ...place.value, ...one }) })),
)

/* *Compare with…*: straight to the cell's one other image, else the pick. */
function compareWith(): void {
  const where = pick(
    detail.value?.images ?? [],
    place.value.version,
    props.seed,
    detail.value?.compare ?? null,
  )
  if ('compare' in where) compare(where.compare)
  else picking.value = where.at
}

/* Compare carries where this view was opened from, so its esc returns here
   with the same way back. */
function compare(other: CellImage): void {
  void router.push({
    name: 'compare',
    params: { ...props, with: `v${other.version}`, withSeed: other.seed },
    state: { from: window.history.state?.from ?? null },
  })
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
    when: () => (detail.value?.targets.length ?? 0) > 0,
  },
  {
    id: 'compare',
    keys: plain('KeyC'),
    label: 'compare with…',
    run: compareWith,
    when: () => others.value.length > 0,
  },
  {
    id: 'side-by-side',
    keys: [shifted('KeyC')],
    label: 'side by side',
    run: () => (pairing.value = true),
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
            :disabled="!detail.targets.length"
            @click="drafting = true"
          >
            Draft from this<KeyHint command="draft-from" />
          </button>
        </div>
        <div class="large__group">
          <button
            v-if="others.length"
            class="btn btn-secondary"
            type="button"
            data-compare
            @click="compareWith"
          >
            Compare with…<KeyHint command="compare" />
          </button>
          <button
            class="btn btn-secondary"
            type="button"
            data-side-by-side
            @click="pairing = true"
          >
            Side by side<KeyHint command="side-by-side" />
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
      v-if="picking !== null"
      :title="`Compare v${detail.version} · seed ${detail.seed} with…`"
      :images="choices"
      :start="picking"
      @pick="compare"
      @close="picking = null"
    />
    <ImageViewer
      v-if="pairing"
      :images="pair"
      pair
      @close="pairing = false"
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
