<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { assign, hub, prepare, renderOffer, stopJob } from '../api'
import ImportSheet from '../components/ImportSheet.vue'
import RenderDialog from '../components/RenderDialog.vue'
import RefusalPage from '../components/RefusalPage.vue'
import { useLive } from '../composables/useLive'
import { firstFlow, queue } from '../composables/useQueue'
import type { CellEvent, HubCell, HubInfo, HubSource, Stage } from '../types'

/* A batch's hub: its sources by the offered flows, each cell's stage read from
   the run's directory (design spec J2). A tick assigns a flow through the
   server's `assign`; the Prepare bar runs what changed as one job, and its
   progress arrives over `/events`. */
const props = defineProps<{ batch: string }>()
const router = useRouter()
const info = ref<HubInfo | null>(null)
const refusal = ref<string | null>(null)
const grid = ref<HTMLElement | null>(null)
const focus = ref<{ row: number; column: number }>({ row: 0, column: 0 })
const adding = ref(false)
/* The Render dialog is up; it has no URL of its own (design spec §1 rule 8). */
const rendering = ref(false)
/* Why Render is disabled, from the server's quote; null while it is offered. */
const renderBlocked = ref<string | null>(null)

async function checkRender(): Promise<void> {
  try {
    renderBlocked.value = (await renderOffer(props.batch)).disabled
  } catch (reason) {
    renderBlocked.value = (reason as Error).message
  }
}

function openRender(): void {
  if (renderBlocked.value === null) rendering.value = true
}
/* The rows selected with ⇧↑↓; a column is ticked for all of them at once. */
const selected = ref<Set<number>>(new Set())
/* The job slot and billing are the shell's live state; this stream brings cells. */
const { job, billing } = useLive()
/* The Prepare bar's refusal, the CLI's own text (J8a). */
const barRefusal = ref<string | null>(null)
/* Each cell's refusal from a tick or from the job, by `source|flow`. */
const refusals = ref<Record<string, string>>({})
/* The stage running in a cell, by `source|flow`, from the job's reports. */
const running = ref<Record<string, string>>({})
let stream: EventSource | null = null

/* Add sources commits into this batch, and the grid is read again. */
async function added(): Promise<void> {
  adding.value = false
  info.value = await hub(props.batch)
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
/* A render holds the one slot: Prepare waits, with its reason. */
const blocked = computed(() => job.value?.state === 'running' && job.value.kind === 'render')

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
const bar = computed(() => busy.value || changes.value.length > 0 || barRefusal.value !== null)

/* A cell's key in the maps of refusals and running stages. */
function at(name: string, flow: string): string {
  return `${name}|${flow}`
}

function key(source: HubSource, flow: string): string {
  return at(source.name, flow)
}

function cell(source: HubSource, flow: string): HubCell {
  return source.cells[flow] ?? { stage: null, renders: 0, refusal: null, status: null }
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

function review(source: HubSource, flow: string): void {
  if (reviewable(source, flow))
    void router.push({
      name: 'review',
      params: { batch: props.batch, digest: source.digest, flow },
    })
}

function apply(name: string, flow: string, found: HubCell): void {
  const source = sources.value.find((one) => one.name === name)
  if (source) source.cells = { ...source.cells, [flow]: found }
}

/* Tick or untick `flow` for `targets`, each answered on its own. */
async function tick(targets: HubSource[], flow: string, remove: boolean): Promise<void> {
  const names = targets.filter((one) => !locked(cell(one, flow))).map((one) => one.name)
  if (names.length === 0) return
  try {
    const answered = await assign(props.batch, names, flow, remove)
    for (const [name, found] of Object.entries(answered.cells)) {
      apply(name, flow, found)
      delete refusals.value[at(name, flow)]
    }
    for (const [name, message] of Object.entries(answered.refused))
      refusals.value[at(name, flow)] = message
  } catch (reason) {
    barRefusal.value = (reason as Error).message
  }
}

/* Space on a cell: tick it, or untick it while it is only assigned. With rows
   selected, the focused column is ticked for every one of them. */
function toggle(row: number, column: number): void {
  const flow = flows.value[column]
  if (!flow) return
  if (selected.value.size > 0) {
    const rows = [...selected.value].map((index) => sources.value[index]).filter(Boolean)
    const unticked = rows.some((one) => cell(one, flow).stage === null)
    void tick(rows, flow, !unticked)
    return
  }
  const source = sources.value[row]
  if (!source) return
  const found = cell(source, flow)
  if (locked(found)) return
  void tick([source], flow, found.stage === 'assigned')
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
    await stopJob()
  } catch (reason) {
    barRefusal.value = (reason as Error).message
  }
}

/* Discard unticks every pending cell that holds no work yet. */
function discard(): void {
  barRefusal.value = null
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

/* ↑↓←→ move between cells, space ticks, ⇧↑↓ selects rows, ↵ opens the focused
   cell's Review, ⌘↵ Prepare, ⌥2 Review next, ⌥A Add sources, esc clears the
   selection. Matched on `event.code`, because Option types a character on macOS. */
function onKey(event: KeyboardEvent): void {
  if (adding.value || rendering.value) return
  const { row, column } = focus.value
  if (event.altKey && event.code === 'Digit2') {
    event.preventDefault()
    reviewNext()
    return
  }
  if (event.altKey && event.code === 'KeyA') {
    event.preventDefault()
    adding.value = true
    return
  }
  if (event.altKey && event.code === 'KeyR') {
    event.preventDefault()
    openRender()
    return
  }
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    event.preventDefault()
    void runPrepare()
    return
  }
  if (event.altKey || event.metaKey || event.ctrlKey) return
  if (event.shiftKey && (event.key === 'ArrowDown' || event.key === 'ArrowUp')) {
    event.preventDefault()
    select(event.key === 'ArrowDown' ? 1 : -1)
    return
  }
  const moves: Record<string, [number, number]> = {
    ArrowUp: [-1, 0],
    ArrowDown: [1, 0],
    ArrowLeft: [0, -1],
    ArrowRight: [0, 1],
  }
  const move = moves[event.key]
  if (move) {
    event.preventDefault()
    place(row + move[0], column + move[1])
  } else if (event.key === ' ') {
    event.preventDefault()
    toggle(row, column)
  } else if (event.key === 'Escape') {
    selected.value = new Set()
  } else if (event.key === 'Enter') {
    const here = sources.value[row]
    if (here) review(here, flows.value[column])
  }
}

/* The stream: a snapshot on every connect, then each report as it happens. */
function listen(): void {
  stream = new EventSource(`/events?${new URLSearchParams({ batch: props.batch })}`)
  stream.addEventListener('snapshot', (event) => {
    const data = JSON.parse((event as MessageEvent<string>).data) as { hub?: HubInfo }
    if (data.hub) info.value = data.hub
  })
  stream.addEventListener('cell', (event) => {
    const data = JSON.parse((event as MessageEvent<string>).data) as CellEvent
    const here = at(data.source, data.flow)
    apply(data.source, data.flow, data.cell)
    if (data.state === 'start') running.value[here] = data.stage
    else delete running.value[here]
    if (data.state === 'refused' && data.message) refusals.value[here] = data.message
    else if (data.state === 'done') delete refusals.value[here]
  })
}

/* A job that ends changes the cells and what Render offers. */
watch(job, (slot, before) => {
  if (slot?.state === 'failed' && slot.kind === 'prepare') barRefusal.value = slot.message
  if (before?.state === 'running' && slot?.state !== 'running') {
    running.value = {}
    void hub(props.batch).then((read) => (info.value = read))
    void checkRender()
  }
})

/* A pod alert raised or cleared changes what Render offers. */
watch(billing, () => void checkRender())

onMounted(async () => {
  window.addEventListener('keydown', onKey)
  try {
    info.value = await hub(props.batch)
  } catch (reason) {
    refusal.value = (reason as Error).message
    return
  }
  listen()
  void checkRender()
  place(0, 0)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  stream?.close()
})
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <section v-else-if="info" class="hub">
    <ImportSheet v-if="adding" :batch="batch" @close="adding = false" @imported="added" />
    <RenderDialog
      v-if="rendering"
      :batch="batch"
      @close="(rendering = false), void checkRender()"
    />
    <div class="hub__head">
      <span class="mono">{{ sources.length }} sources × {{ flows.length }} flows</span>
      <button class="btn btn-secondary hub__add" type="button" @click="adding = true">
        Add sources…<span class="appbar__key">⌥A</span>
      </button>
      <button
        v-if="next"
        class="btn"
        :class="bar ? 'btn-secondary' : 'btn-primary'"
        type="button"
        @click="reviewNext"
      >
        Review next · {{ next.source.name }} {{ next.flow }}<span class="appbar__key">⌥2</span>
      </button>
      <span v-else class="hub__reason">nothing left to review</span>
      <span v-if="renderBlocked" class="hub__reason" data-render-reason>{{ renderBlocked }}</span>
      <button
        class="btn btn-secondary"
        type="button"
        data-render
        :disabled="renderBlocked !== null"
        @click="openRender"
      >
        Render…<span class="appbar__key">⌥R</span>
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
        @click="toggle(focus.row, column)"
      >
        {{ flow }}
      </button>
      <template v-for="(source, row) in sources" :key="source.name">
        <div class="hub__source" :class="{ 'hub__source--selected': selected.has(row) }">
          <span class="hub__name mono">
            <input
              v-if="selected.size > 0"
              class="hub__tick"
              type="checkbox"
              :checked="selected.has(row)"
              :aria-label="`select ${source.name}`"
              @change="selected.has(row) ? selected.delete(row) : selected.add(row)"
            />{{ source.name }}
          </span>
          <span class="hub__file mono">
            {{ source.name }}<template v-if="source.width"> · {{ source.width }}×{{ source.height }}</template>
          </span>
          <span v-if="source.carries.length" class="hub__warn mono">⚠ not cleaned</span>
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
          @click="place(row, column)"
          @dblclick="review(source, flow)"
        >
          <input
            class="hub__tick"
            :class="{ 'hub__tick--assigned': cell(source, flow).stage === 'assigned' }"
            type="checkbox"
            :checked="cell(source, flow).stage !== null"
            :disabled="locked(cell(source, flow))"
            :aria-label="`${source.name} × ${flow}`"
            @click.prevent="toggle(row, column)"
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
              v-if="focus.row === row && focus.column === column && reviewable(source, flow)"
              class="hub__action mono"
              >↵ review</span
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
    <p class="hub__keys mono">
      ↑↓←→ move · space tick / untick · ⇧↑↓ select rows · ↵ the cell's review · ⌥A add sources ·
      ⌥2 review next · ⌥R render · ⌥0 library
    </p>
    <div v-if="bar" class="prepare-bar">
      <template v-if="busy">
        <span class="prepare-bar__cells mono">
          Prepare · {{ job?.stage }} · {{ job?.flow }}
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
