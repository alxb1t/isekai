<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { draftFrom, hub, imageAt, photoUrl, renderDetail, versionOf } from '../api'
import { type CellImage, others as othersOf, pick } from '../cells'
import ComparePick from '../components/ComparePick.vue'
import ImageViewer from '../components/ImageViewer.vue'
import KeyHint from '../components/KeyHint.vue'
import RefusalPage from '../components/RefusalPage.vue'
import ReviseConfirm from '../components/ReviseConfirm.vue'
import { useKeys } from '../composables/useKeys'
import { plain, shifted } from '../stores/keys'
import type { RenderDetail } from '../types'

/* An image's large view (design spec J5·2): the image on `ground-media`, the
   sheet it was rendered from beside it — filled fields only, read-only. ⇧E
   revises it; c compares it with another image of its cell, picked in a dialog
   of tiles (J5·8); ⇧C sets it beside its run's photograph; ⇧F drafts the first
   target from its approval. */
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
const revising = ref(false)
const checkingRevision = ref(false)
/* Why drafting a target from this image's approval was refused, or null. */
const drafting = ref<string | null>(null)
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

/* `conjure-anime-wai` -> `Conjure from this`. */
function fromThis(flow: string): string {
  const [word] = flow.split('-')
  return `${word.charAt(0).toUpperCase()}${word.slice(1)} from this`
}

/* A rendered flow with a later draft is re-opened. Read its current state
   before asking to write, so an existing correction opens without a confirm. */
async function reviseImage(): Promise<void> {
  if (checkingRevision.value) return
  checkingRevision.value = true
  drafting.value = null
  try {
    const grid = await hub(props.collection)
    const cell = grid.sources.find((one) => one.digest === props.digest)?.cells[props.flow]
    if (cell?.status === 're-opened') {
      await router.push({
        name: 'review',
        params: { collection: props.collection, digest: props.digest, flow: props.flow },
      })
    } else revising.value = true
  } catch (reason) {
    drafting.value = (reason as Error).message
  } finally {
    checkingRevision.value = false
  }
}

/* No confirm: the draft is one Discard draft away, and costs nothing. A waiting
   draft with edits of its own is answered rather than replaced, and opened. */
async function draftTarget(target: string): Promise<void> {
  drafting.value = null
  try {
    await draftFrom(
      { ...place.value, flow: target },
      props.flow,
      place.value.version,
      props.seed,
    )
    void router.push({
      name: 'review',
      params: { collection: props.collection, digest: props.digest, flow: target },
    })
  } catch (reason) {
    drafting.value = (reason as Error).message
  }
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
    id: 'revise',
    keys: [shifted('KeyE')],
    label: 'revise',
    run: () => void reviseImage(),
  },
  {
    id: 'draft-from',
    keys: [shifted('KeyF')],
    label: 'draft from this',
    run: () => void draftTarget(detail.value?.targets[0] ?? ''),
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
          <button class="btn btn-secondary" type="button" data-revise @click="reviseImage">
            Revise this image<KeyHint command="revise" />
          </button>
          <button
            v-for="(target, index) in detail.targets"
            :key="target"
            class="btn btn-secondary"
            type="button"
            data-draft-from
            @click="draftTarget(target)"
          >
            {{ fromThis(target) }}<KeyHint v-if="index === 0" command="draft-from" />
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
      <p v-if="drafting" class="renders__refusal" data-draft-refusal>
        <span class="refusal__mark" />{{ drafting }}
      </p>
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
    <ReviseConfirm
      v-if="revising"
      :collection="collection"
      :images="[{ digest, flow, version: place.version, seed }]"
      @close="revising = false"
    />
  </section>
</template>
