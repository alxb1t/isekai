<script lang="ts">
import { noun } from '../words'

/** Return the Prepare bar's line: the photographs its changes prepare, each once.

    e.g. ["ada.jpg", "ada.jpg", "bea.jpg"], "b" -> "2 photographs to prepare in b" */
export function toPrepare(sources: string[], collection: string): string {
  const count = new Set(sources).size
  return `${count} ${noun(count, 'photograph')} to prepare in ${collection}`
}

/** Return the Prepare button's words: the changes it runs. e.g. 4 -> "4 changes · Prepare" */
export function prepareButton(changes: number): string {
  return `${changes} ${noun(changes, 'change')} · Prepare`
}
</script>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { bar as barOf, dismiss, failed, held, prepared, progress } from '../bars'
import {
  type CellGrid,
  EMPTY_CELL,
  type PickTile,
  action,
  cellGrid,
  cellOrder,
  clicks,
  locked,
  pending,
  ready,
  targets,
} from '../cells'
import { assign, prepare, sourceAt, sourceThumbAt, thumbAt } from '../api'
import CellModal from '../components/CellModal.vue'
import ImageViewer, { type Shown } from '../components/ImageViewer.vue'
import ImportSheet from '../components/ImportSheet.vue'
import KeyHint from '../components/KeyHint.vue'
import RenderBar from '../components/RenderBar.vue'
import RenderDialog from '../components/RenderDialog.vue'
import RefusalPage from '../components/RefusalPage.vue'
import { useEdges } from '../composables/useEdges'
import { useKeys } from '../composables/useKeys'
import { clamp, kept } from '../grid'
import { at, useCollectionStore } from '../stores/collection'
import { isControl, modded, plain, shifted } from '../stores/keys'
import { useLiveStore } from '../stores/live'
import type { HubCell, HubSource, Stage } from '../types'

/* A collection's hub: its sources by the offered flows, each cell's stage read from
   the run's directory (design spec J2). A tick assigns a flow through the
   server's `assign`; the Prepare bar runs what changed as one job, and its
   progress arrives over `/events`. */
const props = defineProps<{ collection: string }>()
const router = useRouter()
const refusal = ref<string | null>(null)
const grid = ref<HTMLElement | null>(null)
const page = ref<HTMLElement | null>(null)
const reveal = useEdges(() => page.value)
const focus = ref<{ row: number; column: number }>({ row: 0, column: 0 })
const adding = ref(false)
/* The photographs the viewer shows, and from where; or null. */
const viewing = ref<{ images: Shown[]; start: number } | null>(null)
/* The cell the cell modal shows: its source's name and digest, and its grid; or null. */
const modal = ref<{ title: string; digest: string; grid: CellGrid } | null>(null)
/* The collection's hub, its running cells and refusals, and its Render offer, shared
   with every screen of the collection and kept live from the page's one stream. */
const store = useCollectionStore()
const { hub: info, running, refusals, offer, dialog, rendering, plan, preparing: busy } =
  storeToRefs(store)

/* Render opens only from its own bar: while changes wait, Prepare holds it. */
function openRender(): void {
  if (shown.value === 'render') store.openDialog()
}
/* The rows selected with ⇧↑↓; a column is ticked for all of them at once. */
const selected = ref<Set<number>>(new Set())
/* Prepare has its own slot: a render running beside it holds nothing back. */
const live = useLiveStore()
const { jobs } = storeToRefs(live)
const { prepareTotals } = live
/* Another collection's running Prepare, which disables this one's, with its reason. */
const prepareHeld = computed(() => held(jobs.value.prepare, props.collection))
/* The running Prepare's stages done over the stages asked; null slides the line. */
const filled = computed(() => progress(prepared(jobs.value.prepare)))
/* The Prepare bar's refusal, the CLI's own text (J8a). */
const barRefusal = ref<string | null>(null)

/* Add sources commits into this collection, and the grid is read again. */
async function added(): Promise<void> {
  adding.value = false
  await store.reloadHub()
}

/* The six segments of a stage track, and how many each stage has done. A draft
   shares the sheet's segment. */
const SEGMENTS = ['assigned', 'tag', 'caption', 'sheet', 'approved', 'rendered'] as const
const DONE: Record<Stage, number> = {
  assigned: 1,
  tagged: 2,
  sheet: 4,
  draft: 4,
  approved: 5,
  rendered: 6,
  unreadable: 0,
}
/* A running stage's segment, and the word its cell shows. */
const RUNNING: Record<string, { segment: number; word: string }> = {
  tag: { segment: 1, word: 'tagging…' },
  caption: { segment: 2, word: 'captioning…' },
  sheet: { segment: 3, word: 'filling the sheet…' },
}

const flows = computed(() => info.value?.flows ?? [])
const sources = computed(() => info.value?.sources ?? [])

/* What Prepare would run: every pending cell. */
const changes = computed(() =>
  sources.value.flatMap((source) =>
    flows.value
      .filter((flow) => pending(cell(source, flow)))
      .map((flow) => ({ source, flow })),
  ),
)
/* The one bar the hub shows: Prepare first, then Render, then none. */
const shown = computed(() =>
  barOf({
    changes: changes.value.length,
    preparing: busy.value || barRefusal.value !== null,
    images: offer.value.images + offer.value.others,
    refused: offer.value.refused !== null,
    rendering: rendering.value,
    plan: plan.value,
  }),
)

/* A source's display name: its file's name without the extension. */
function stem(name: string): string {
  const dot = name.lastIndexOf('.')
  return dot > 0 ? name.slice(0, dot) : name
}

function key(source: HubSource, flow: string): string {
  return at(source.name, flow)
}

function cell(source: HubSource, flow: string): HubCell {
  return source.cells[flow] ?? EMPTY_CELL
}

/* Whether the focus is on `row` at grid column `column`: 0 the source, the flows from 1. */
function focused(row: number, column: number): boolean {
  return focus.value.row === row && focus.value.column === column
}

function word(source: HubSource, flow: string): string {
  const stage = running.value[key(source, flow)]
  if (stage) return RUNNING[stage]?.word ?? `${stage}…`
  const found = cell(source, flow)
  if (found.stage === 'rendered') return `rendered ×${found.renders}`
  return found.stage ?? ''
}

function segment(source: HubSource, flow: string, index: number): string {
  const stage = running.value[key(source, flow)]
  if (stage && RUNNING[stage]?.segment === index) return 'hub__segment--running'
  const found = cell(source, flow).stage
  return found && index < DONE[found] ? 'hub__segment--done' : ''
}

function reviewable(source: HubSource, flow: string): boolean {
  return source.digest !== null && cell(source, flow).status !== null
}

/* The focused cell's action hint, or null where it offers none here. */
function hint(source: HubSource, flow: string): string | null {
  const found = action(cell(source, flow))
  if (found.action === 'review' || found.action === 'sheet')
    return reviewable(source, flow) ? found.hint : null
  return found.hint
}

function review(source: HubSource, flow: string): void {
  if (reviewable(source, flow))
    void router.push({
      name: 'review',
      params: { collection: props.collection, digest: source.digest, flow },
    })
}

/* The collection's photographs in the viewer, from the row's. */
function viewSource(row: number): void {
  viewing.value = {
    images: sources.value.map((one) => ({
      src: sourceAt(props.collection, one.name),
      name: one.name,
      width: one.width,
      height: one.height,
    })),
    start: row,
  }
}

/* A cell's images in the cell modal, on `at` or its newest. Its grid is taken once,
   so a render landing meanwhile moves nothing under the focus. */
function view(
  source: HubSource,
  flow: string,
  at?: { version: number; seed: string },
): void {
  const { digest } = source
  const found = cell(source, flow)
  const start = at ?? found.newest
  if (digest === null || start === null || found.images.length === 0) return
  modal.value = { title: source.name, digest, grid: cellGrid(flow, found.images, start) }
}

/* A cell modal tile's thumbnail, under its source's `digest`. */
const tileThumb = (digest: string) => (tile: NonNullable<PickTile>) =>
  thumbAt({ collection: props.collection, digest, ...tile })

/* ↵ or a click in the cell modal opens that image's large view, whose Esc comes back here. */
function openLarge(tile: NonNullable<PickTile>): void {
  const held = modal.value
  if (held === null) return
  void router.push({
    name: 'render',
    params: {
      collection: props.collection,
      digest: held.digest,
      ...tile,
      version: `v${tile.version}`,
    },
  })
}

/* A click or ↵ on a cell: whatever its stage offers. A click ticks its own cell
   alone; ↵, as space, the selected rows. */
function act(row: number, column: number, pointer = false): void {
  const source = sources.value[row]
  const flow = flows.value[column - 1]
  if (!source || !flow) return
  const kind = action(cell(source, flow)).action
  if (kind === 'tick') toggle(row, column, pointer)
  else if (kind === 'review' || kind === 'sheet') review(source, flow)
  else if (kind === 'view') view(source, flow)
}

/* Tick or untick `flow` for `targets`, each answered on its own. */
async function tick(targets: HubSource[], flow: string, remove: boolean): Promise<void> {
  const names = targets.filter((one) => !locked(cell(one, flow))).map((one) => one.name)
  if (names.length === 0) return
  try {
    const answered = await assign(props.collection, names, flow, remove)
    for (const [name, found] of Object.entries(answered.cells)) {
      store.apply(name, flow, found)
      delete refusals.value[at(name, flow)]
    }
    for (const [name, message] of Object.entries(answered.refused))
      refusals.value[at(name, flow)] = message
  } catch (reason) {
    barRefusal.value = (reason as Error).message
  }
}

/* Space on a cell: tick it, or untick it while it is pending. With rows
   selected, the focused column is ticked for every one of them; a pointer's
   click ticks its own cell alone. The source column ticks nothing. */
function toggle(row: number, column: number, pointer = false): void {
  const flow = flows.value[column - 1]
  if (!flow) return
  const rows = targets(selected.value, row, pointer)
    .map((index) => sources.value[index])
    .filter((one): one is HubSource => one !== undefined)
  if (rows.length === 0) return
  const unticked = rows.some((one) => cell(one, flow).stage === null)
  void tick(rows, flow, !unticked)
}

/* A pointer's click on a cell; one on its refusal, or ending a text selection,
   leaves it as it is. Column 0 is the source's; the flows' start at 1. */
function clicked(event: MouseEvent, row: number, column: number): void {
  place(row, column)
  if (clicks(event.target as Element | null, window.getSelection()?.toString() ?? ''))
    act(row, column, true)
}

async function runPrepare(): Promise<void> {
  if (busy.value || prepareHeld.value !== null || changes.value.length === 0) return
  barRefusal.value = null
  try {
    live.hold((await prepare(props.collection)).job)
  } catch (reason) {
    barRefusal.value = (reason as Error).message
  }
}

async function stop(): Promise<void> {
  try {
    await live.stop('prepare')
  } catch (reason) {
    barRefusal.value = (reason as Error).message
  }
}

/* Discard unticks every pending cell that holds no work yet, and dismisses this
   collection's failed Prepare, so a hub opened again in this page does not show it. */
function discard(): void {
  barRefusal.value = null
  dismiss(jobs.value.prepare, props.collection)
  for (const flow of flows.value) {
    const rows = sources.value.filter((one) => pending(cell(one, flow)))
    if (rows.length) void tick(rows, flow, true)
  }
}

/* A cell's name in the store's focus: its source's and its flow's, the source
   column's flow empty. */
function named(spot: { row: number; column: number }): string {
  return at(sources.value[spot.row]?.name ?? '', flows.value[spot.column - 1] ?? '')
}

/* Focus a cell and scroll it into view: a click `nearest`, a key's move by the
   edges' rule, a restored focus to the window's centre, where the eye finds it. */
function place(
  row: number,
  column: number,
  how: ScrollIntoViewOptions | 'key' = { block: 'nearest' },
): void {
  const rows = sources.value.length
  if (rows === 0) return
  focus.value = {
    row: clamp(row, rows - 1),
    column: clamp(column, flows.value.length),
  }
  store.focus.hub = named(focus.value)
  void nextTick(() => {
    const cell = focusedCell()
    if (!cell) return
    cell.focus({ preventScroll: true })
    if (how === 'key') reveal(cell, focus.value.row, rows)
    else cell.scrollIntoView(how)
  })
}

/* The focused cell's element, once drawn. */
function focusedCell(): HTMLElement | null | undefined {
  return grid.value?.querySelector<HTMLElement>(
    `[data-row="${focus.value.row}"][data-column="${focus.value.column}"]`,
  )
}

/* ⇧↑↓ extends the selection from the focused row, which joins it. */
function select(step: number): void {
  const { row, column } = focus.value
  const target = Math.min(Math.max(row + step, 0), sources.value.length - 1)
  selected.value = new Set([...selected.value, row, target])
  place(target, column, 'key')
}

const moveBy = (rows: number, columns: number) => () =>
  place(focus.value.row + rows, focus.value.column + columns, 'key')

/* ↵ and Space are the grid's unless a button or a link holds the focus, which
   answers them itself. */
const onGrid = () => !isControl(document.activeElement)
const onSource = () => focus.value.column === 0

/* h j k l or the arrows move between cells, ⇧J ⇧K or ⇧↓ ⇧↑ select rows, and
   esc clears the selection (D25). */
useKeys('screen', [
  { id: 'add', keys: [shifted('KeyA')], label: 'add sources', run: () => (adding.value = true) },
  { id: 'render', keys: [shifted('KeyG')], label: 'render', run: openRender },
  { id: 'prepare', keys: [modded('Enter')], label: 'prepare', run: () => void runPrepare() },
  { id: 'left', keys: plain('KeyH', 'ArrowLeft'), label: 'left', run: moveBy(0, -1) },
  { id: 'down', keys: plain('KeyJ', 'ArrowDown'), label: 'down', run: moveBy(1, 0) },
  { id: 'up', keys: plain('KeyK', 'ArrowUp'), label: 'up', run: moveBy(-1, 0) },
  { id: 'right', keys: plain('KeyL', 'ArrowRight'), label: 'right', run: moveBy(0, 1) },
  {
    id: 'select-down',
    keys: [shifted('KeyJ'), shifted('ArrowDown')],
    label: 'select rows down',
    run: () => select(1),
  },
  {
    id: 'select-up',
    keys: [shifted('KeyK'), shifted('ArrowUp')],
    label: 'select rows up',
    run: () => select(-1),
  },
  {
    id: 'tick',
    keys: plain('Space'),
    label: 'tick / untick',
    run: () => toggle(focus.value.row, focus.value.column),
    when: onGrid,
  },
  {
    id: 'photo',
    keys: plain('Enter'),
    label: 'view photo',
    run: () => viewSource(focus.value.row),
    when: () => onGrid() && onSource(),
  },
  {
    id: 'act',
    keys: plain('Enter'),
    label: "the cell's action",
    run: () => act(focus.value.row, focus.value.column),
    when: onGrid,
  },
  {
    id: 'clear',
    keys: plain('Escape'),
    label: 'clear the selection',
    run: () => (selected.value = new Set()),
  },
])

/* A failed Prepare is shown, the one that ended before this hub opened too. */
watch(
  () => jobs.value.prepare,
  (slot) => {
    const message = failed(slot, props.collection)
    if (message !== null) barRefusal.value = message
  },
  { immediate: true },
)

onMounted(async () => {
  void store.check()
  try {
    await store.reloadHub()
  } catch (reason) {
    refusal.value = (reason as Error).message
    return
  }
  const spots = sources.value.flatMap((_, row) =>
    Array.from({ length: flows.value.length + 1 }, (_, column) => ({ row, column })),
  )
  // A large view's Esc, Back to Hub and Delete send the cell of the image it closed, by digest
  // and flow, read once, so a later visit to this entry keeps where the focus last was.
  const sent = window.history.state?.cell as { digest: string; flow: string } | undefined
  if (sent) window.history.replaceState({ ...window.history.state, cell: undefined }, '')
  const deletedFrom = sent
    ? spots.find(
        ({ row, column }) =>
          sources.value[row]?.digest === sent.digest && flows.value[column - 1] === sent.flow,
      )
    : undefined
  const spot = deletedFrom ?? kept(spots, named, store.focus.hub)
  if (spot) place(spot.row, spot.column, { block: 'center' })
})

/* The Render dialog is this page's: leaving the page closes it. */
onUnmounted(() => {
  if (dialog.value) store.closeDialog()
})
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <section v-else-if="info" ref="page" class="hub">
    <ImportSheet v-if="adding" :collection="collection" @close="adding = false" @imported="added" />
    <ImageViewer
      v-if="viewing"
      :images="viewing.images"
      :start="viewing.start"
      @close="viewing = null"
    />
    <CellModal
      v-if="modal"
      :title="modal.title"
      :grid="modal.grid"
      :src="tileThumb(modal.digest)"
      @open="openLarge"
      @close="modal = null"
    />
    <RenderDialog v-if="dialog" @close="store.closeDialog" />
    <div class="hub__head">
      <span class="mono">
        {{ sources.length }} {{ noun(sources.length, 'source') }} ×
        {{ flows.length }} {{ noun(flows.length, 'flow') }}
      </span>
      <button class="btn btn-secondary hub__add" type="button" @click="adding = true">
        Add sources…<KeyHint command="add" />
      </button>
    </div>
    <div
      ref="grid"
      class="hub__grid"
      :style="{ gridTemplateColumns: `250px repeat(${flows.length}, 1fr)` }"
    >
      <span class="section-label hub__label">source</span>
      <button
        v-for="(flow, column) in flows"
        :key="flow"
        class="hub__label hub__column mono"
        type="button"
        :disabled="selected.size === 0"
        @click="toggle(focus.row, column + 1)"
      >
        {{ flow }}
      </button>
      <template v-for="(source, row) in sources" :key="source.name">
        <div
          class="hub__source"
          :class="{
            'hub__source--selected': selected.has(row),
            'hub__cell--focused': focused(row, 0),
          }"
          :data-row="row"
          data-column="0"
          tabindex="-1"
          @click="place(row, 0)"
        >
          <span class="hub__about">
            <span class="hub__name mono">
              <input
                v-if="selected.size > 0"
                class="hub__tick"
                type="checkbox"
                :checked="selected.has(row)"
                :aria-label="`select ${source.name}`"
                @change="selected.has(row) ? selected.delete(row) : selected.add(row)"
              />{{ stem(source.name) }}
            </span>
            <span v-if="source.carries.length" class="hub__warn mono">⚠ not cleaned</span>
          </span>
          <span v-if="focused(row, 0)" class="hub__action mono">↵ view photo</span>
          <button
            class="hub__thumb"
            type="button"
            :aria-label="`view ${source.name}`"
            @click="viewSource(row)"
          >
            <img :src="sourceThumbAt(collection, source.name)" alt="" loading="lazy" />
          </button>
        </div>
        <div
          v-for="(flow, column) in flows"
          :key="flow"
          class="hub__cell"
          :class="{ 'hub__cell--focused': focused(row, column + 1) }"
          :data-row="row"
          :data-column="column + 1"
          :data-source="source.name"
          :data-flow="flow"
          :data-stage="cell(source, flow).stage ?? 'none'"
          tabindex="-1"
          @click="clicked($event, row, column + 1)"
        >
          <span class="hub__line">
            <input
              class="hub__tick"
              :class="{ 'hub__tick--pending': pending(cell(source, flow)) }"
              type="checkbox"
              :checked="cell(source, flow).stage !== null"
              :disabled="locked(cell(source, flow))"
              :aria-label="`${source.name} × ${flow}`"
              @click.prevent.stop="place(row, column + 1), toggle(row, column + 1, true)"
            />
            <template v-if="cell(source, flow).stage !== null">
              <span class="hub__track">
                <span
                  v-for="(name, index) in SEGMENTS"
                  :key="name"
                  class="hub__segment"
                  :class="segment(source, flow, index)"
                />
              </span>
              <span
                class="hub__word mono"
                :class="{ 'hub__word--running': running[key(source, flow)] }"
                >{{ word(source, flow) }}</span
              >
              <span
                v-if="focused(row, column + 1) && hint(source, flow)"
                class="hub__action mono"
                >{{ hint(source, flow) }}</span
              >
            </template>
          </span>
          <p v-if="cell(source, flow).refusal" class="hub__refusal">
            <span class="refusal__mark" />{{ cell(source, flow).refusal }}
          </p>
          <p v-if="refusals[key(source, flow)]" class="hub__refusal">
            <span class="refusal__mark" />{{ refusals[key(source, flow)] }}
          </p>
          <span
            v-if="
              source.digest && (cell(source, flow).images.length || ready(cell(source, flow)))
            "
            class="hub__images"
          >
            <button
              v-for="one in cellOrder(cell(source, flow).images)"
              :key="`${one.version}/${one.seed}`"
              class="tile"
              type="button"
              :data-version="one.version"
              :data-seed="one.seed"
              @click.stop="place(row, column + 1), view(source, flow, one)"
            >
              <img
                :src="thumbAt({ collection, digest: source.digest, flow, ...one })"
                :alt="`${source.name} ${flow} v${one.version} seed ${one.seed}`"
                loading="lazy"
              />
              <span class="tile__badge mono">v{{ one.version }}</span>
            </button>
            <span
              v-if="ready(cell(source, flow))"
              class="tile tile--ready mono"
              data-ready
              >{{ ready(cell(source, flow)) }}</span
            >
          </span>
        </div>
      </template>
    </div>
    <RenderBar
      v-if="shown === 'render' || shown === 'session'"
      :images="offer.images"
      :others="offer.others"
      :disabled="offer.disabled"
      :refused="offer.refused"
      :rendering="rendering"
      @open="openRender"
    />
    <div
      v-else-if="shown === 'prepare'"
      class="prepare-bar"
      :class="{ running: busy, 'prepare-bar--sized': busy && filled !== null }"
      :style="busy && filled !== null ? { '--progress': `${filled * 100}%` } : undefined"
    >
      <template v-if="busy">
        <span class="prepare-bar__cells mono">
          Prepare · {{ prepareTotals(jobs.prepare) }}
        </span>
        <button class="btn btn-secondary" type="button" @click="stop">Stop</button>
      </template>
      <template v-else>
        <p v-if="barRefusal" class="prepare-bar__refusal">
          <span class="refusal__mark" />{{ barRefusal }}
        </p>
        <span v-else class="prepare-bar__cells mono">
          {{ toPrepare(changes.map((one) => one.source.name), collection) }}
        </span>
        <button class="btn btn-secondary" type="button" @click="discard">Discard</button>
        <span v-if="prepareHeld" class="hub__reason" data-prepare-reason>{{ prepareHeld }}</span>
        <button
          class="btn btn-primary"
          type="button"
          :disabled="changes.length === 0 || prepareHeld !== null"
          @click="runPrepare"
        >
          {{ prepareButton(changes.length) }}<span
            class="appbar__key"
            >⌘↵</span
          >
        </button>
      </template>
    </div>
  </section>
</template>
