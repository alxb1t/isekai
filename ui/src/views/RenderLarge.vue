<script lang="ts">
/** Return a guard for work that must not finish once the view is left: `begin()` hands back a check
    that holds until the next `begin()` or `drop()`. e.g. `const ok = g.begin(); g.drop(); ok()` -> false */
export function latest(): { begin: () => () => boolean; drop: () => void } {
  let current = 0
  return {
    begin: () => {
      const mine = ++current
      return () => mine === current
    },
    drop: () => {
      current += 1
    },
  }
}
</script>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  bakeAt,
  bakeDetail,
  deleteRender,
  imageAt,
  photoUrl,
  renderDetail,
  thumbAt,
  versionOf,
} from '../api'
import { offered } from '../bakes'
import { type PickTile, placeOf, rowOrder, sourceGrid, stepped } from '../cells'
import BakeChain from '../components/BakeChain.vue'
import ComparePick from '../components/ComparePick.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import DraftDialog from '../components/DraftDialog.vue'
import KeyHint from '../components/KeyHint.vue'
import RefusalPage from '../components/RefusalPage.vue'
import { deletion } from '../confirm'
import { useKeys } from '../composables/useKeys'
import { useCollectionStore } from '../stores/collection'
import { plain, shifted } from '../stores/keys'
import type { Bake, RenderDetail } from '../types'
import { offerTo } from '../viewkey'

/* An image's large view (design spec J5·2): the image on `ground-media`, the
   sheet it was rendered from beside it — filled fields only, read-only. ⇧D
   drafts a flow from it, its own a revision (J5·3); ⇧C compares it with any
   image of its source, the photograph among them, picked in a grid (J5·8).
   ⇧P opens the placement screen's first step on it. ⇧⌫ asks, then deletes the render and opens the Hub on its cell.
   `h` `l` walk the photograph's row; esc goes back to the Hub, on the shown image's cell.
   With `k` it is a bake's view: the bake's image and record, and none of the writes, *Place a tattoo* among them. */
const props = defineProps<{
  collection: string
  digest: string
  flow: string
  version: string
  seed: string
  k?: string
}>()
const router = useRouter()
const store = useCollectionStore()
const detail = ref<RenderDetail | null>(null)
const bake = ref<Bake | null>(null)
const refusal = ref<string | null>(null)
const drafting = ref(false)
/* The pick of an image to compare with, while it is open. */
const picking = ref(false)
const deleting = ref(false)

const place = computed(() => ({
  collection: props.collection,
  digest: props.digest,
  flow: props.flow,
  version: versionOf(props.version),
  seed: props.seed,
}))

/* The address's params without `k`: the render, compare and compare-photo routes have none. */
const params = computed(() => ({
  collection: props.collection,
  digest: props.digest,
  flow: props.flow,
  version: props.version,
  seed: props.seed,
}))

const clock = (at: number) =>
  new Date(at * 1000).toLocaleTimeString('en-GB', { hour12: false })

/* The bake's number, or null on the render's own address. */
const shown = computed(() => (props.k === undefined ? null : Number(props.k)))

/* The image drawn: the render's, a baked bake's own, and for a queued one the image it was placed on. */
const media = computed(() => {
  const held = bake.value
  if (shown.value === null || held === null) return imageAt(place.value)
  const at = held.state === 'queued' ? held.placed_on : shown.value
  return at === null ? imageAt(place.value) : bakeAt(place.value, at)
})

const placedOn = (one: Bake) => (one.placed_on === null ? 'the render' : `edit ${one.placed_on}`)

const grid = computed(() => (detail.value ? sourceGrid(detail.value) : null))

/* A tile's thumbnail: the photograph's own bytes, else the render's thumbnail. */
const tileSrc = (tile: PickTile) =>
  tile === null ? photoUrl(place.value) : thumbAt({ ...place.value, ...tile })

function compare(other: PickTile): void {
  void router.push(
    other === null
      ? { name: 'compare-photo', params: params.value }
      : {
          name: 'compare',
          params: {
            ...params.value,
            withFlow: other.flow,
            withVersion: `v${other.version}`,
            withSeed: other.seed,
          },
        },
  )
}

/* The images `h` `l` step through, and where this one stands among them. */
const order = computed(() => (detail.value ? rowOrder(detail.value) : []))
const index = computed(() => placeOf(order.value, place.value))

/* Show the image `by` steps away in place of this one; held at either end. */
function step(by: -1 | 1): void {
  const next = stepped(order.value, place.value, by)
  if (next === null) return
  void router.replace({
    name: 'render',
    params: { ...params.value, flow: next.flow, version: `v${next.version}`, seed: next.seed },
  })
}

/* The Hub, focused on the shown image's cell, named by digest: the view knows it,
   not the source's name `store.focus.hub` keys on. `h` `l` cross flows, so the
   cell may not be the one this view was opened from. */
const hubCell = computed(() => ({
  name: 'hub',
  params: { collection: props.collection },
  state: { cell: { digest: props.digest, flow: props.flow } },
}))

/* The hub is read again first, so the Hub draws without the deleted render; a refusal opens it all the same.
   The Hub, focused on the deleted render's cell, unless the operator has left this view meanwhile. */
const leaving = latest()
onUnmounted(leaving.drop)
async function deleted(): Promise<void> {
  const still = leaving.begin()
  await store.reloadHub().catch(() => undefined)
  if (still()) void router.push(hubCell.value)
}

useKeys('screen', [
  { id: 'previous', keys: plain('KeyH', 'ArrowLeft'), label: 'previous image', run: () => step(-1) },
  { id: 'next', keys: plain('KeyL', 'ArrowRight'), label: 'next image', run: () => step(1) },
  {
    id: 'draft-from',
    keys: [shifted('KeyD')],
    label: 'draft from this',
    run: () => (drafting.value = true),
    when: () => offered(props.k) && detail.value !== null,
  },
  {
    id: 'compare',
    keys: [shifted('KeyC')],
    label: 'compare with…',
    run: () => (picking.value = true),
    when: () => offered(props.k) && grid.value !== null,
  },
  {
    id: 'place',
    keys: [shifted('KeyP')],
    label: 'place a tattoo',
    run: () => void router.push(offerTo(props)),
    when: () => offered(props.k) && detail.value !== null,
  },
  {
    id: 'delete',
    keys: [shifted('Backspace')],
    label: 'delete this render',
    run: () => (deleting.value = true),
    when: () => offered(props.k) && detail.value !== null,
  },
  {
    id: 'back',
    keys: plain('Escape'),
    label: 'back',
    run: () => void router.push(hubCell.value),
  },
])

onMounted(async () => {
  try {
    detail.value = await renderDetail(place.value)
    if (shown.value !== null) bake.value = await bakeDetail(place.value, shown.value)
  } catch (reason) {
    refusal.value = (reason as Error).message
  }
})
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <section v-else-if="detail" class="large">
    <div class="large__media">
      <img :src="media" :alt="k === undefined ? `seed ${detail.seed}` : `edit ${k} of seed ${detail.seed}`" />
    </div>
    <aside class="large__sheet" data-sheet>
      <span class="section-label">
        {{ detail.flow }} · v{{ detail.version }} · seed {{ detail.seed
        }}<template v-if="index >= 0">
          · {{ index + 1 }} of {{ order.length }}</template
        >
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
      <p v-if="detail.damaged" class="large__refusal">
        <span class="refusal__mark" />{{ detail.damaged }}
      </p>
      <img class="large__photo" :src="photoUrl(place)" alt="the photograph" data-photo />
      <div class="large__actions">
        <div v-if="offered(k)" class="large__group">
          <button
            class="btn btn-secondary"
            type="button"
            data-draft-from
            @click="drafting = true"
          >
            Draft from this<KeyHint command="draft-from" />
          </button>
        </div>
        <div v-if="offered(k)" class="large__group">
          <button
            class="btn btn-secondary"
            type="button"
            data-compare
            @click="picking = true"
          >
            Compare with…<KeyHint command="compare" />
          </button>
        </div>
        <div v-if="offered(k)" class="large__group">
          <RouterLink class="btn btn-secondary" :to="offerTo(props)" data-place
            >Place a tattoo<KeyHint command="place"
          /></RouterLink>
        </div>
        <div v-if="offered(k)" class="large__group">
          <button
            class="btn btn-secondary"
            type="button"
            data-delete
            @click="deleting = true"
          >
            Delete<KeyHint command="delete" />
          </button>
        </div>
        <div class="large__group">
          <RouterLink class="btn btn-secondary" :to="hubCell"
            >Back to Hub<KeyHint command="back" /></RouterLink
          >
        </div>
      </div>
      <BakeChain v-if="detail.bakes.length" :bakes="detail.bakes" :shown="shown" :params="params" />
      <template v-if="bake">
        <p v-if="bake.state === 'queued'" class="large__head mono" data-queued>
          queued · the image it was placed on, until the next session bakes it
        </p>
        <dl class="large__fields" data-bake-record>
          <dt class="mono">placed on</dt>
          <dd>{{ placedOn(bake) }}</dd>
          <dt class="mono">edit</dt>
          <dd>{{ bake.edit }}</dd>
          <dt class="mono">baked</dt>
          <dd>{{ bake.baked_at === null ? 'queued' : clock(bake.baked_at) }}</dd>
        </dl>
      </template>
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
    <ConfirmDialog
      v-if="deleting"
      marker="delete"
      :title="deletion.title"
      :name="deletion.name"
      :run="() => deleteRender(place)"
      @close="deleting = false"
      @done="deleted"
    />
  </section>
</template>
