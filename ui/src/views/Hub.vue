<script setup lang="ts">
import { noun } from '../words'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { bar as barOf, dismiss, failed } from '../bars'
import { action, clicks, targets } from '../cells'
import { assign, prepare, sourceAt, sourceThumbAt } from '../api'
import ImageViewer from '../components/ImageViewer.vue'
import ImportSheet from '../components/ImportSheet.vue'
import KeyBar from '../components/KeyBar.vue'
import KeyHint from '../components/KeyHint.vue'
import RenderBar from '../components/RenderBar.vue'
import RenderDialog from '../components/RenderDialog.vue'
import RefusalPage from '../components/RefusalPage.vue'
import { useKeys } from '../composables/useKeys'
import { firstFlow, queue } from '../composables/useQueue'
import { at, useBatchStore } from '../stores/batch'
import { modded, plain, shifted } from '../stores/keys'
import { useLiveStore } from '../stores/live'
import type { HubCell, HubSource, Stage } from '../types'

/* A batch's hub: its sources by the offered flows, each cell's stage read from
   the run's directory (design spec J2). A tick assigns a flow through the
   server's `assign`; the Prepare bar runs what changed as one job, and its
   progress arrives over `/events`. */
const props = defineProps<{ batch: string }>()
const router = useRouter()
const refusal = ref<string | null>(null)
const grid = ref<HTMLElement | null>(null)
const focus = ref<{ row: number; column: number }>({ row: 0, column: 0 })
const adding = ref(false)
/* The source open in the viewer, or null. */
const viewing = ref<HubSource | null>(null)
/* The batch's hub, its running cells and refusals, and its Render offer, shared
   with every screen of the batch and kept live from the page's one stream. */
const store = useBatchStore()
const { hub: info, running, refusals, offer, dialog, rendering } = storeToRefs(store)

/* Render opens only from its own bar: while changes wait, Prepare holds it. */
function openRender(): void {
  if (shown.value === 'render') store.openDialog()
}
/* The rows selected with ⇧↑↓; a column is ticked for all of them at once. */
const selected = ref<Set<number>>(new Set())
/* A render holds the one slot, so Prepare waits while it is `blocked`. */
const live = useLiveStore()
const { job, renderRunning: blocked } = storeToRefs(live)
const { prepareTotals } = live
/* The Prepare bar's refusal, the CLI's own text (J8a). */
const barRefusal = ref<string | null>(null)

/* Add sources commits into this batch, and the grid is read again. */
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
const busy = computed(() => job.value?.state === 'running' && job.value.kind === 'prepare')

/* Review next: the first unapproved sheet of the first flow that has any. */
const next = computed(() => {
  const held = info.value
  const flow = held ? firstFlow(held) : null
  if (!held || !flow) return null
  const digest = queue(held, flow)[0]
  const source = held.sources.find((one) => one.digest === digest)
  return source ? { source, flow } : null
})

/* What Prepare would run: every assigned cell with no sheet. */
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
    images: offer.value.images,
    refused: offer.value.refused !== null,
    rendering: rendering.value,
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
  return (
    source.cells[flow] ?? { stage: null, renders: 0, refusal: null, status: null, newest: null }
  )
}

function pending(found: HubCell): boolean {
  return found.stage === 'assigned' || found.stage === 'tagged'
}

/* A tick can be taken back only while the cell is assigned: past it, it stays. */
function locked(found: HubCell): boolean {
  return found.stage !== null && found.stage !== 'assigned'
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
      params: { batch: props.batch, digest: source.digest, flow },
    })
}

/* The large view of a cell's newest image; Esc there comes back here. */
function view(source: HubSource, flow: string): void {
  const newest = cell(source, flow).newest
  if (source.digest === null || newest === null) return
  void router.push({
    name: 'render',
    params: {
      batch: props.batch,
      digest: source.digest,
      flow,
      version: `v${newest.version}`,
      seed: newest.seed,
    },
    state: { from: 'hub' },
  })
}

/* A click or ↵ on a cell: whatever its stage offers. A click ticks its own cell
   alone; ↵, as space, the selected rows. */
function act(row: number, column: number, pointer = false): void {
  const source = sources.value[row]
  const flow = flows.value[column]
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
    const answered = await assign(props.batch, names, flow, remove)
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

/* Space on a cell: tick it, or untick it while it is only assigned. With rows
   selected, the focused column is ticked for every one of them; a pointer's
   click ticks its own cell alone. */
function toggle(row: number, column: number, pointer = false): void {
  const flow = flows.value[column]
  if (!flow) return
  const rows = targets(selected.value, row, pointer)
    .map((index) => sources.value[index])
    .filter((one): one is HubSource => one !== undefined)
  if (rows.length === 0) return
  const unticked = rows.some((one) => cell(one, flow).stage === null)
  void tick(rows, flow, !unticked)
}

/* A pointer's click on a cell; one on its refusal, or ending a text selection,
   leaves it as it is. */
function clicked(event: MouseEvent, row: number, column: number): void {
  place(row, column)
  if (clicks(event.target as Element | null, window.getSelection()?.toString() ?? ''))
    act(row, column, true)
}

async function runPrepare(): Promise<void> {
  if (busy.value || blocked.value || changes.value.length === 0) return
  barRefusal.value = null
  try {
    job.value = (await prepare(props.batch)).job
  } catch (reason) {
    barRefusal.value = (reason as Error).message
  }
}

async function stop(): Promise<void> {
  try {
    await live.stop()
  } catch (reason) {
    barRefusal.value = (reason as Error).message
  }
}

/* Discard unticks every pending cell that holds no work yet, and dismisses this
   batch's failed Prepare, so a hub opened again in this page does not show it. */
function discard(): void {
  barRefusal.value = null
  dismiss(job.value, props.batch)
  for (const flow of flows.value) {
    const rows = sources.value.filter((one) => cell(one, flow).stage === 'assigned')
    if (rows.length) void tick(rows, flow, true)
  }
}

function place(row: number, column: number): void {
  const rows = sources.value.length
  const columns = flows.value.length
  if (rows === 0 || columns === 0) return
  focus.value = {
    row: Math.min(Math.max(row, 0), rows - 1),
    column: Math.min(Math.max(column, 0), columns - 1),
  }
  void nextTick(() =>
    grid.value
      ?.querySelector<HTMLElement>(
        `[data-row="${focus.value.row}"][data-column="${focus.value.column}"]`,
      )
      ?.focus(),
  )
}

function reviewNext(): void {
  if (next.value) review(next.value.source, next.value.flow)
}

/* ⇧↑↓ extends the selection from the focused row, which joins it. */
function select(step: number): void {
  const { row, column } = focus.value
  const target = Math.min(Math.max(row + step, 0), sources.value.length - 1)
  selected.value = new Set([...selected.value, row, target])
  place(target, column)
}

const free = () => !adding.value && !dialog.value && !viewing.value
const moveBy = (rows: number, columns: number) => () =>
  place(focus.value.row + rows, focus.value.column + columns)

/* h j k l or the arrows move between cells, ⇧J ⇧K or ⇧↓ ⇧↑ select rows, and
   esc clears the selection (D25). */
useKeys(
  'screen',
  [
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
    },
    {
      id: 'act',
      keys: plain('Enter'),
      label: "the cell's action",
      run: () => act(focus.value.row, focus.value.column),
    },
    {
      id: 'clear',
      keys: plain('Escape'),
      label: 'clear the selection',
      run: () => (selected.value = new Set()),
    },
  ].map((command) => ({ ...command, when: free })),
)

/* A failed Prepare is shown, the one that ended before this hub opened too. */
watch(
  job,
  (slot) => {
    const message = failed(slot, props.batch)
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
  place(0, 0)
})
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <section v-else-if="info" class="hub">
    <ImportSheet v-if="adding" :batch="batch" @close="adding = false" @imported="added" />
    <ImageViewer
      v-if="viewing"
      :src="sourceAt(batch, viewing.name)"
      :name="viewing.name"
      :width="viewing.width"
      :height="viewing.height"
      @close="viewing = null"
    />
    <RenderDialog v-if="dialog" :batch="batch" @close="store.closeDialog" />
    <div class="hub__head">
      <span class="mono">
        {{ sources.length }} {{ noun(sources.length, 'source') }} ×
        {{ flows.length }} {{ noun(flows.length, 'flow') }}
      </span>
      <button class="btn btn-secondary hub__add" type="button" @click="adding = true">
        Add sources…<KeyHint command="add" />
      </button>
      <button
        v-if="next"
        class="btn"
        :class="shown ? 'btn-secondary' : 'btn-primary'"
        type="button"
        @click="reviewNext"
      >
        Review next · {{ next.source.name }} {{ next.flow }}<KeyHint command="review" />
      </button>
      <span v-else class="hub__reason">nothing left to review</span>
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
        @click="toggle(focus.row, column)"
      >
        {{ flow }}
      </button>
      <template v-for="(source, row) in sources" :key="source.name">
        <div class="hub__source" :class="{ 'hub__source--selected': selected.has(row) }">
          <button
            class="hub__thumb"
            type="button"
            :aria-label="`view ${source.name}`"
            @click="viewing = source"
          >
            <img :src="sourceThumbAt(batch, source.name)" alt="" loading="lazy" />
          </button>
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
            <span class="hub__file mono">
              {{ source.name }}<template v-if="source.width"> · {{ source.width }}×{{ source.height }}</template>
            </span>
            <span v-if="source.carries.length" class="hub__warn mono">⚠ not cleaned</span>
          </span>
        </div>
        <div
          v-for="(flow, column) in flows"
          :key="flow"
          class="hub__cell"
          :class="{ 'hub__cell--focused': focus.row === row && focus.column === column }"
          :data-row="row"
          :data-column="column"
          :data-source="source.name"
          :data-flow="flow"
          :data-stage="cell(source, flow).stage ?? 'none'"
          tabindex="-1"
          @click="clicked($event, row, column)"
        >
          <input
            class="hub__tick"
            :class="{ 'hub__tick--assigned': cell(source, flow).stage === 'assigned' }"
            type="checkbox"
            :checked="cell(source, flow).stage !== null"
            :disabled="locked(cell(source, flow))"
            :aria-label="`${source.name} × ${flow}`"
            @click.prevent.stop="place(row, column), toggle(row, column, true)"
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
              v-if="focus.row === row && focus.column === column && locked(cell(source, flow))"
              class="hub__reason"
              >prepared · the tick stays</span
            >
            <span
              v-if="focus.row === row && focus.column === column && hint(source, flow)"
              class="hub__action mono"
              >{{ hint(source, flow) }}</span
            >
            <p v-if="cell(source, flow).refusal" class="hub__refusal">
              <span class="refusal__mark" />{{ cell(source, flow).refusal }}
            </p>
          </template>
          <p v-if="refusals[key(source, flow)]" class="hub__refusal">
            <span class="refusal__mark" />{{ refusals[key(source, flow)] }}
          </p>
        </div>
      </template>
    </div>
    <KeyBar />
    <RenderBar
      v-if="shown === 'render'"
      :images="offer.images"
      :disabled="offer.disabled"
      :refused="offer.refused"
      :rendering="rendering"
      @open="openRender"
    />
    <div v-else-if="shown === 'prepare'" class="prepare-bar" :class="{ running: busy }">
      <template v-if="busy">
        <span class="prepare-bar__cells mono">
          Prepare · {{ prepareTotals(job) }}
        </span>
        <button class="btn btn-secondary" type="button" @click="stop">Stop</button>
      </template>
      <template v-else>
        <p v-if="barRefusal" class="prepare-bar__refusal">
          <span class="refusal__mark" />{{ barRefusal }}
        </p>
        <span v-else class="prepare-bar__cells mono">
          {{ changes.map((one) => `${one.source.name} × ${one.flow}`).join(' · ') }}
        </span>
        <button class="btn btn-secondary" type="button" @click="discard">Discard</button>
        <span v-if="blocked" class="hub__reason">A render is running</span>
        <button
          class="btn btn-primary"
          type="button"
          :disabled="changes.length === 0 || blocked"
          @click="runPrepare"
        >
          {{ changes.length }} {{ changes.length === 1 ? 'change' : 'changes' }} · Prepare<span
            class="appbar__key"
            >⌘↵</span
          >
        </button>
      </template>
    </div>
  </section>
</template>
