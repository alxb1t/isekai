<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { hub } from '../api'
import ImportSheet from '../components/ImportSheet.vue'
import RefusalPage from '../components/RefusalPage.vue'
import { firstFlow, queue } from '../composables/useQueue'
import type { HubCell, HubInfo, HubSource, Stage } from '../types'

/* A batch's hub: its sources by its tracked flows, each cell's stage read from
   the run's directory (design spec J2). Read-only: a tick is assigned by a
   stage verb, so every checkbox is disabled and says why. */
const props = defineProps<{ batch: string }>()
const router = useRouter()
const info = ref<HubInfo | null>(null)
const refusal = ref<string | null>(null)
const grid = ref<HTMLElement | null>(null)
const focus = ref<{ row: number; column: number }>({ row: 0, column: 0 })
const adding = ref(false)

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

const flows = computed(() => info.value?.flows ?? [])

/* Review next: the first unapproved sheet of the first flow that has any. */
const next = computed(() => {
  const held = info.value
  const flow = held ? firstFlow(held) : null
  if (!held || !flow) return null
  const digest = queue(held, flow)[0]
  const source = held.sources.find((one) => one.digest === digest)
  return source ? { source, flow } : null
})
const sources = computed(() => info.value?.sources ?? [])

function cell(source: HubSource, flow: string): HubCell {
  return source.cells[flow] ?? { stage: null, renders: 0, refusal: null, status: null }
}

function word(found: HubCell): string {
  if (found.stage === 'rendered') return `rendered ×${found.renders}`
  return found.stage ?? ''
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

/* ↑↓←→ move between cells, ↵ opens the focused cell's Review, ⌥2 Review next.
   Matched on `event.code`, because Option types a character on macOS. */
function onKey(event: KeyboardEvent): void {
  const { row, column } = focus.value
  if (adding.value) return
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
  if (event.altKey || event.metaKey || event.ctrlKey) return
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
  } else if (event.key === 'Enter') {
    const here = sources.value[row]
    if (here) review(here, flows.value[column])
  }
}

onMounted(async () => {
  window.addEventListener('keydown', onKey)
  try {
    info.value = await hub(props.batch)
  } catch (reason) {
    refusal.value = (reason as Error).message
    return
  }
  place(0, 0)
})

onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <section v-else-if="info" class="hub">
    <ImportSheet v-if="adding" :batch="batch" @close="adding = false" @imported="added" />
    <div class="hub__head">
      <span class="mono">{{ sources.length }} sources × {{ flows.length }} flows</span>
      <button class="btn btn-secondary hub__add" type="button" @click="adding = true">
        Add sources…<span class="appbar__key">⌥A</span>
      </button>
      <button v-if="next" class="btn btn-primary" type="button" @click="reviewNext">
        Review next · {{ next.source.name }} {{ next.flow }}<span class="appbar__key">⌥2</span>
      </button>
      <span v-else class="hub__reason">nothing left to review</span>
    </div>
    <div
      ref="grid"
      class="hub__grid"
      :style="{ gridTemplateColumns: `250px repeat(${flows.length}, 1fr)` }"
    >
      <span class="section-label hub__label">source</span>
      <span v-for="flow in flows" :key="flow" class="hub__label mono">{{ flow }}</span>
      <template v-for="(source, row) in sources" :key="source.name">
        <div class="hub__source">
          <span class="hub__name mono">{{ source.name }}</span>
          <span class="hub__file mono">
            {{ source.name }}<template v-if="source.width"> · {{ source.width }}×{{ source.height }}</template>
          </span>
        </div>
        <div
          v-for="(flow, column) in flows"
          :key="flow"
          class="hub__cell"
          :class="{ 'hub__cell--focused': focus.row === row && focus.column === column }"
          :data-row="row"
          :data-column="column"
          :data-stage="cell(source, flow).stage ?? 'none'"
          tabindex="-1"
          @click="place(row, column)"
          @dblclick="review(source, flow)"
        >
          <template v-if="cell(source, flow).stage === null">
            <input class="hub__tick" type="checkbox" disabled />
            <span class="hub__reason">assigned by a stage verb</span>
          </template>
          <template v-else>
            <input class="hub__tick" type="checkbox" checked disabled />
            <span class="hub__track">
              <span
                v-for="(segment, index) in SEGMENTS"
                :key="segment"
                class="hub__segment"
                :class="{ 'hub__segment--done': index < DONE[cell(source, flow).stage as Stage] }"
              />
            </span>
            <span class="hub__word mono">{{ word(cell(source, flow)) }}</span>
            <span
              v-if="focus.row === row && focus.column === column && reviewable(source, flow)"
              class="hub__action mono"
              >↵ review</span
            >
            <p v-if="cell(source, flow).refusal" class="hub__refusal">
              <span class="refusal__mark" />{{ cell(source, flow).refusal }}
            </p>
          </template>
        </div>
      </template>
    </div>
    <p class="hub__keys mono">↑↓←→ move · ↵ the cell's review · ⌥2 review next · ⌥0 library</p>
  </section>
</template>
