<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { bar } from '../bars'
import { sourceAt, sourceThumbAt, thumbAt } from '../api'
import ImageViewer from '../components/ImageViewer.vue'
import KeyHint from '../components/KeyHint.vue'
import RefusalPage from '../components/RefusalPage.vue'
import RenderBar from '../components/RenderBar.vue'
import RenderDialog from '../components/RenderDialog.vue'
import ReviseConfirm from '../components/ReviseConfirm.vue'
import { useKeys } from '../composables/useKeys'
import { type Move, kept, moved } from '../grid'
import { useBatchStore } from '../stores/batch'
import { plain, shifted } from '../stores/keys'
import { noun } from '../words'
import type { RenderVersion, RevisedImage } from '../types'

/* Renders: a grid of sources by flows, each cell one row of its images, its
   versions oldest to newest, each image marked with its version (design spec
   J5·1). ↵ or a click opens an image's large view; space selects, and e revises
   the selection (§7). A seed rendered under two versions is marked ⇄. The Render
   bar offers what the newest approvals lack; a source, its row's first column,
   opens in the viewer on ↵ or a click on its thumbnail. */
const props = defineProps<{ batch: string }>()
const router = useRouter()
const refusal = ref<string | null>(null)
const focus = ref<{ row: number; column: number }>({ row: 0, column: 0 })
/* The selected images, each as `key` spells it. */
const selected = ref(new Set<string>())
const revising = ref(false)
/* The source open in the viewer, by name, or null. */
const viewing = ref<string | null>(null)
/* The batch's images and its Render offer, shared with every screen of the batch;
   a job's end reads both again. */
const store = useBatchStore()
const { renders: info, offer, dialog, rendering } = storeToRefs(store)
const shown = computed(() =>
  bar({
    changes: 0,
    preparing: false,
    images: offer.value.images,
    refused: offer.value.refused !== null,
    rendering: rendering.value,
  }),
)

interface Spot {
  digest: string
  flow: string
  version: number
  seed: string
}

/* Each cell's versions as they are drawn, oldest first, by source row then flow.
   The payload lists them newest first, which a living scenario holds. */
const oldest = computed<Record<string, RenderVersion[]>[]>(() =>
  (info.value?.sources ?? []).map((source) =>
    Object.fromEntries(
      (info.value?.flows ?? []).map((flow) => [flow, [...(source.cells[flow] ?? [])].reverse()]),
    ),
  ),
)

/* Each source's images in the order they are drawn: flow, oldest version, seed. */
const rows = computed<Spot[][]>(() => {
  const held = info.value
  if (!held) return []
  return held.sources.map((source, row) =>
    source.digest === null
      ? []
      : held.flows.flatMap((flow) =>
          oldest.value[row][flow].flatMap((version) =>
            version.rendered.map((seed) => ({
              digest: source.digest as string,
              flow,
              version: version.version,
              seed,
            })),
          ),
        ),
  )
})

/* The focused image, as `spot` spells it. e.g. "0|summon-anime-wai|1|42" */
const focused = computed(() => {
  const one = here()
  return one ? spot(focus.value.row, one.flow, one.version, one.seed) : ''
})

function spot(row: number, flow: string, version: number, seed: string): string {
  return `${row}|${flow}|${version}|${seed}`
}

/* An image as the selection holds it. e.g. "0d4b…|summon-anime-wai|1|42" */
const key = (one: Spot) => `${one.digest}|${one.flow}|${one.version}|${one.seed}`

const chosen = computed<RevisedImage[]>(() =>
  rows.value.flat().filter((one) => selected.value.has(key(one))),
)

function toggle(one: Spot): void {
  const next = new Set(selected.value)
  if (!next.delete(key(one))) next.add(key(one))
  selected.value = next
}

/* The seeds each cell renders under more than one version, by `digest|flow`. */
const shared = computed(() => {
  const found = new Map<string, Set<string>>()
  for (const source of info.value?.sources ?? [])
    for (const [flow, versions] of Object.entries(source.cells))
      found.set(`${source.digest}|${flow}`, repeated(versions))
  return found
})

function repeated(versions: RenderVersion[]): Set<string> {
  const seen = new Map<string, number>()
  for (const version of versions)
    for (const seed of version.rendered) seen.set(seed, (seen.get(seed) ?? 0) + 1)
  return new Set([...seen].filter(([, count]) => count > 1).map(([seed]) => seed))
}

/* A source's spot, as the store keeps it. e.g. "source|hal.jpg" */
const sourceKey = (name: string) => `source|${name}`

/* Focus `spot`, and keep it in the store for this grid's next opening. */
function hold(spot: { row: number; column: number }): void {
  focus.value = spot
  const one = here()
  const source = info.value?.sources[spot.row]
  if (one) store.focus.renders = key(one)
  else if (source) store.focus.renders = sourceKey(source.name)
}

function go(move: Move): () => void {
  return () => {
    // A row's last column is its image count: column 0 is its source.
    hold(
      moved(
        rows.value.map((spots) => spots.length),
        focus.value,
        move,
      ),
    )
    void nextTick(() =>
      document
        .querySelector<HTMLElement>('.renders__image--focused, .renders__source--focused')
        ?.scrollIntoView({ block: 'nearest' }),
    )
  }
}

/* The focused image; column 0 is its row's source. */
const here = (): Spot | undefined => rows.value[focus.value.row]?.[focus.value.column - 1]
const onSource = (row: number) => focus.value.row === row && focus.value.column === 0

/* h l and the arrows step images, crossing cells into the source; j k between rows (D25). */
useKeys('screen', [
  { id: 'left', keys: plain('KeyH', 'ArrowLeft'), label: 'previous image', run: go('column-') },
  { id: 'right', keys: plain('KeyL', 'ArrowRight'), label: 'next image', run: go('column+') },
  { id: 'down', keys: plain('KeyJ', 'ArrowDown'), label: 'next source', run: go('row+') },
  { id: 'up', keys: plain('KeyK', 'ArrowUp'), label: 'previous source', run: go('row-') },
  {
    id: 'select',
    keys: plain('Space'),
    label: 'select',
    run: () => toggle(here() as Spot),
    when: () => here() !== undefined,
  },
  {
    id: 'open',
    keys: plain('Enter'),
    label: 'open',
    run: () => {
      const one = here()
      if (one) open(focus.value.row, one)
      else viewing.value = info.value?.sources[focus.value.row]?.name ?? null
    },
    when: () => here() !== undefined || focus.value.column === 0,
  },
  {
    id: 'revise',
    keys: [shifted('KeyE')],
    label: 'revise',
    run: () => (revising.value = true),
    when: () => chosen.value.length > 0,
  },
  { id: 'render', keys: [shifted('KeyG')], label: 'render', run: () => store.openDialog() },
])

function thumb(digest: string, flow: string, version: number, seed: string): string {
  return thumbAt({ batch: props.batch, digest, flow, version, seed })
}

/* The large view of `one`, in row `row`, which takes the focus first. */
function open(row: number, one: Spot): void {
  hold({ row, column: rows.value[row].findIndex((spot) => key(spot) === key(one)) + 1 })
  const { digest, flow, version, seed } = one
  void router.push({
    name: 'render',
    params: { batch: props.batch, digest, flow, version: `v${version}`, seed },
  })
}

onMounted(async () => {
  void store.check()
  try {
    await store.reloadRenders()
  } catch (reason) {
    refusal.value = (reason as Error).message
    return
  }
  // Images first, so a grid opened afresh focuses its first image, not a source.
  const images = rows.value.flatMap((held, row) =>
    held.map((one, column) => ({ row, column: column + 1, name: key(one) })),
  )
  const sources = (info.value?.sources ?? []).map((source, row) => ({
    row,
    column: 0,
    name: sourceKey(source.name),
  }))
  const spot = kept([...images, ...sources], ({ name }) => name, store.focus.renders)
  if (spot) hold({ row: spot.row, column: spot.column })
})

/* The Render dialog is this page's: leaving the page closes it. */
onUnmounted(() => {
  if (dialog.value) store.closeDialog()
})
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <section v-else-if="info" class="renders">
    <div class="renders__bar">
      <button
        class="btn btn-secondary"
        type="button"
        data-revise
        :disabled="!chosen.length"
        @click="revising = true"
      >
        Revise {{ chosen.length || '' }}<KeyHint command="revise" />
      </button>
      <span v-if="!chosen.length" class="renders__reason">No image selected</span>
    </div>
    <div
      class="renders__grid"
      :style="{ gridTemplateColumns: `calc(var(--tile-width) + 20px) repeat(${info.flows.length}, 1fr)` }"
    >
      <span class="section-label">source</span>
      <span v-for="flow in info.flows" :key="flow" class="section-label">{{ flow }}</span>
      <template v-for="(source, row) in info.sources" :key="source.name">
        <div
          class="renders__source"
          :class="{ 'renders__source--focused': onSource(row) }"
          :data-row="row"
          data-source
        >
          <button
            class="hub__thumb"
            type="button"
            :aria-label="source.name"
            data-source-thumb
            @click="viewing = source.name"
          >
            <img :src="sourceThumbAt(batch, source.name)" alt="" loading="lazy" />
          </button>
        </div>
        <div v-for="flow in info.flows" :key="flow" class="renders__cell">
          <span class="renders__images">
            <!-- A damaged version's striped tile leads its images, which stay drawn
                 because `rows` moves the focus across them. -->
            <template v-for="version in oldest[row][flow]" :key="version.version">
              <span
                v-if="version.damaged"
                class="renders__image renders__image--damaged"
                :data-version="version.version"
                data-damaged
              >
                <span class="renders__badge mono">v{{ version.version }}</span>
              </span>
              <button
                v-for="seed in version.rendered"
                :key="seed"
                class="renders__image"
                :class="{
                  'renders__image--focused': focused === spot(row, flow, version.version, seed),
                  'renders__image--selected':
                    source.digest &&
                    selected.has(
                      key({ digest: source.digest, flow, version: version.version, seed }),
                    ),
                }"
                type="button"
                :data-version="version.version"
                :data-seed="seed"
                @click="
                  source.digest &&
                  open(row, { digest: source.digest, flow, version: version.version, seed })
                "
              >
                <img
                  v-if="source.digest"
                  :src="thumb(source.digest, flow, version.version, seed)"
                  :alt="`${source.name} ${flow} v${version.version} seed ${seed}`"
                />
                <span class="renders__badge mono"
                  >v{{ version.version }}
                  <span
                    v-if="shared.get(`${source.digest}|${flow}`)?.has(seed)"
                    class="renders__shared"
                    data-shared
                    >⇄</span
                  ></span
                >
              </button>
            </template>
            <span
              v-if="(source.ready[flow] ?? 0) > 0"
              class="renders__image renders__image--ready mono"
              data-ready
              >ready · {{ source.ready[flow] }} {{ noun(source.ready[flow], 'image') }}</span
            >
          </span>
          <p
            v-for="version in oldest[row][flow].filter((one) => one.damaged)"
            :key="version.version"
            class="renders__refusal"
          >
            <span class="refusal__mark" />v{{ version.version }} · {{ version.damaged }}
          </p>
        </div>
      </template>
    </div>
    <ImageViewer
      v-if="viewing"
      :images="[{ src: sourceAt(batch, viewing), name: viewing }]"
      @close="viewing = null"
    />
    <ReviseConfirm
      v-if="revising"
      :batch="batch"
      :images="chosen"
      @close="revising = false"
    />
    <RenderBar
      v-if="shown === 'render'"
      :images="offer.images"
      :disabled="offer.disabled"
      :refused="offer.refused"
      :rendering="rendering"
      @open="store.openDialog"
    />
    <RenderDialog v-if="dialog" :batch="batch" @close="store.closeDialog" />
  </section>
</template>
