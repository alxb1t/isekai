<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { imageAt, photoUrl, thumbAt } from '../api'
import ImageViewer, { type Shown } from '../components/ImageViewer.vue'
import KeyHint from '../components/KeyHint.vue'
import RefusalPage from '../components/RefusalPage.vue'
import { useKeys } from '../composables/useKeys'
import type { Focus } from '../grid'
import { type Step, asked, first, grid, lasted, outcome, stepped } from '../sessions'
import { useBatchStore } from '../stores/batch'
import { plain } from '../stores/keys'
import { alerting, clock, useLiveStore } from '../stores/live'
import type { SessionImage } from '../types'

/* One render session (design spec J4·2, J4·3), from the record its verb writes.
   While the render slot runs it, the slot adds the volume steps and Stop, and the
   page is drawn from the slot until the verb has written the record. Its images
   are a grid: a column per photograph, a row per flow, the photographs' row last,
   a waiting tile per image to come. h j k l or the arrows move, the first render
   focused on opening; ↵ opens the viewer over the row. No spend is shown after
   the quote. */
const props = defineProps<{ batch: string; id: string }>()
const store = useBatchStore()
const live = useLiveStore()
const { session: record } = storeToRefs(store)
const { jobs, billing, now } = storeToRefs(live)
const refusal = ref<string | null>(null)
const stopRefusal = ref<string | null>(null)

/* The render slot's session, while it is this one. */
const slot = computed(() => {
  const held = jobs.value.render
  return held?.batch === props.batch && held.session?.id === props.id ? held : null
})
const running = computed(() => record.value?.outcome === 'running' || slot.value?.state === 'running')
const alert = computed(() => alerting(billing.value))

const started = computed(() => record.value?.started ?? slot.value?.session?.started ?? null)
const limit = computed(() => record.value?.limit ?? slot.value?.session?.limit ?? 0)
const of = computed(() => (record.value ? asked(record.value) : (slot.value?.session?.of ?? 0)))
const images = computed(() => record.value?.images ?? [])
const done = computed(() => images.value.length)
const steps = computed(() => record.value?.steps ?? {})
const volume = computed(() => slot.value?.session?.steps ?? {})

const elapsed = computed(() =>
  started.value
    ? lasted(
        started.value,
        record.value?.ended ?? slot.value?.session?.ended,
        running.value,
        now.value,
      )
    : null,
)

/* The five steps, always, each with its state. */
const shown = computed(() => {
  const rendering =
    of.value > 0 && done.value === of.value
      ? 'done'
      : steps.value.pod === 'ready' && running.value
        ? 'running'
        : ''
  return [
    { name: 'volume up', state: volume.value['volume up'] ?? '' },
    { name: 'pod boot', state: steps.value.pod ?? '' },
    { name: 'rendering', state: rendering, note: `image ${done.value} of ${of.value}` },
    { name: 'teardown', state: steps.value.teardown ?? '' },
    { name: 'volume down', state: volume.value['volume down'] ?? '' },
  ]
})

/* Only when both teardown steps are confirmed and gpunit holds nothing. */
const quiet = computed(
  () => steps.value.teardown === 'done' && volume.value['volume down'] === 'done' && !alert.value,
)
/* Why it failed: the record's word, else the job's before the record was written. */
const failure = computed(() =>
  record.value?.outcome === 'failed'
    ? record.value.message
    : slot.value?.state === 'failed'
      ? slot.value.message
      : null,
)
const ended = computed(() => (running.value || !record.value ? null : outcome(record.value)))

const layout = computed(() =>
  record.value ? grid(record.value) : { digests: [], flows: [], cells: [] },
)
const focus = ref<Focus>({ row: 0, column: 0 })
const focused = (row: number, column: number) =>
  focus.value.row === row && focus.value.column === column

/* A photograph's own flow, any that plans or landed it, for its run's address. */
function photo(column: number): string {
  const row = layout.value.cells.findIndex(
    (cells) => cells[column].images.length > 0 || cells[column].waiting > 0,
  )
  const digest = layout.value.digests[column]
  return photoUrl({ batch: props.batch, digest, flow: layout.value.flows[row] })
}

/* A row's images, left to right, as the viewer steps through them. */
function row(at: number): Shown[] {
  if (at === layout.value.flows.length)
    return layout.value.digests.map((digest, column) => ({ src: photo(column), name: digest }))
  return layout.value.cells[at].flatMap((cell) =>
    cell.images.map((one) => ({
      src: imageAt({ batch: props.batch, ...one }),
      name: `${one.flow} · v${one.version} · seed ${one.seed}`,
    })),
  )
}

/* The row the viewer steps through, and where it starts. */
const viewing = ref<{ row: number; start: number } | null>(null)
const viewed = computed<Shown[]>(() => (viewing.value ? row(viewing.value.row) : []))

/* Open the viewer over `at`'s row, on `one`, else the cell's first image. */
function view(at: Focus, one?: SessionImage): void {
  focus.value = at
  if (at.row === layout.value.flows.length) {
    viewing.value = { row: at.row, start: at.column }
    return
  }
  const before = layout.value.cells[at.row]
    .slice(0, at.column)
    .reduce((sum, cell) => sum + cell.images.length, 0)
  const cell = layout.value.cells[at.row][at.column]
  if (!cell.images.length) return
  viewing.value = { row: at.row, start: before + Math.max(one ? cell.images.indexOf(one) : 0, 0) }
}

function place(at: Focus): void {
  focus.value = at
  void nextTick(() =>
    document
      .querySelector<HTMLElement>(`[data-cell="${at.row}-${at.column}"]`)
      ?.focus(),
  )
}

const go = (step: Step) => () => place(stepped(layout.value, focus.value, step))

useKeys('screen', [
  { id: 'left', keys: plain('KeyH', 'ArrowLeft'), label: 'previous photograph', run: go('photograph-') },
  { id: 'right', keys: plain('KeyL', 'ArrowRight'), label: 'next photograph', run: go('photograph+') },
  { id: 'down', keys: plain('KeyJ', 'ArrowDown'), label: 'next row', run: go('row+') },
  { id: 'up', keys: plain('KeyK', 'ArrowUp'), label: 'previous row', run: go('row-') },
  {
    id: 'open',
    keys: plain('Enter'),
    label: 'the viewer',
    run: () => view(focus.value),
    when: () => layout.value.digests.length > 0,
  },
])

/* The first render takes the focus once the record is read, and holds the tab stop. */
watch(
  () => record.value !== null,
  (read) => {
    if (read && record.value) place(first(layout.value, record.value))
  },
  { immediate: true },
)

async function stop(): Promise<void> {
  try {
    await live.stop('render')
  } catch (reason) {
    stopRefusal.value = (reason as Error).message
  }
}

onMounted(async () => {
  try {
    await store.showSession(props.id)
  } catch (reason) {
    // The job has started and its verb has not written the record yet.
    if (!slot.value) refusal.value = (reason as Error).message
  }
})
</script>

<template>
  <RefusalPage v-if="refusal && !slot && !record" :refusal="refusal" />
  <section v-else-if="record || slot" class="session" :data-session-page="id">
    <span class="section-label">
      Render session · {{ batch }} · {{ of }} image{{ of === 1 ? '' : 's' }}
    </span>
    <p class="session__timer mono" data-session-timer>
      {{ elapsed === null ? '—' : clock(elapsed)
      }}<span class="session__limit"> of {{ clock(limit) }} at most</span>
    </p>
    <div class="session__bar">
      <span
        class="session__fill"
        :style="{ width: `${Math.min(100, ((elapsed ?? 0) / (limit || 1)) * 100)}%` }"
      />
    </div>
    <ol class="session__steps mono">
      <li v-for="step in shown" :key="step.name" :data-step="step.name" :data-state="step.state">
        <span class="session__mark" :class="`session__mark--${step.state || 'waiting'}`" />
        {{ step.name }}
        <span class="session__state">{{ step.note ?? step.state }}</span>
      </li>
    </ol>
    <div
      v-if="layout.digests.length"
      class="session__grid"
      :style="{ gridTemplateColumns: `max-content repeat(${layout.digests.length}, max-content)` }"
      data-session-grid
    >
      <template v-for="(flow, at) in layout.flows" :key="flow">
        <span class="session__flow mono">{{ flow }}</span>
        <div
          v-for="(cell, column) in layout.cells[at]"
          :key="layout.digests[column]"
          class="session__cell"
          :class="{ 'session__cell--focused': focused(at, column) }"
          :data-cell="`${at}-${column}`"
          :tabindex="focused(at, column) ? 0 : -1"
          @click="focus = { row: at, column }"
        >
          <button
            v-for="one in cell.images"
            :key="`${one.version}/${one.seed}`"
            class="session__tile session__tile--done"
            type="button"
            tabindex="-1"
            :aria-label="`view ${one.flow} v${one.version} seed ${one.seed}`"
            data-session-image
            @click.stop="view({ row: at, column }, one)"
          >
            <img :src="thumbAt({ batch, ...one })" alt="" />
          </button>
          <span v-for="index in cell.waiting" :key="`waiting-${index}`" class="session__tile" data-waiting />
        </div>
      </template>
      <span class="session__flow section-label">photographs</span>
      <div
        v-for="(digest, column) in layout.digests"
        :key="digest"
        class="session__cell"
        :class="{ 'session__cell--focused': focused(layout.flows.length, column) }"
        :data-cell="`${layout.flows.length}-${column}`"
        :tabindex="focused(layout.flows.length, column) ? 0 : -1"
      >
        <button
          class="session__tile session__tile--photo"
          type="button"
          tabindex="-1"
          :aria-label="`view the photograph ${digest}`"
          data-session-source
          @click="view({ row: layout.flows.length, column })"
        >
          <img :src="photo(column)" alt="" loading="lazy" />
        </button>
      </div>
    </div>
    <p v-if="failure" class="session__refusal"><span class="refusal__mark" />{{ failure }}</p>
    <p v-if="stopRefusal" class="session__refusal">
      <span class="refusal__mark" />{{ stopRefusal }}
    </p>
    <footer class="session__actions">
      <button v-if="slot?.state === 'running'" class="btn btn-secondary" type="button" @click="stop">
        Stop session now
      </button>
      <template v-if="!running">
        <span v-if="quiet" class="session__quiet" data-quiet>Nothing is billing.</span>
        <span v-if="ended" class="mono" data-outcome>{{ ended }}</span>
        <span class="mono">{{ done }} of {{ of }} rendered</span>
        <RouterLink class="btn btn-primary" data-renders :to="{ name: 'renders', params: { batch } }"
          >View in Renders<KeyHint command="renders" /></RouterLink
        >
      </template>
    </footer>
    <ImageViewer
      v-if="viewing && viewed.length"
      :images="viewed"
      :start="viewing.start"
      @close="viewing = null"
    />
  </section>
</template>
