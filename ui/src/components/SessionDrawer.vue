<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { photoUrl, sourceAt, sourceThumbAt, thumbAt } from '../api'
import ImageViewer from './ImageViewer.vue'
import KeyHint from './KeyHint.vue'
import { useSessionViewer } from '../composables/useSessionViewer'
import { useHeldFocus } from '../composables/useHeldFocus'
import { useKeys } from '../composables/useKeys'
import { type Focus, type Move, moved } from '../grid'
import { asked, first, grid, lastColumns, lasted, outcome } from '../sessions'
import { useDrawerStore } from '../stores/drawer'
import { type Key, isControl, plain, shifted } from '../stores/keys'
import { alerting, clock, useLiveStore } from '../stores/live'
import { noun } from '../words'

/* The render drawer (design spec J4·2, J4·3): the shown session, from the record
   its verb writes, over half the window. While the render slot runs it, the slot
   adds the volume steps and Stop, and the drawer is drawn from the slot until the
   verb has written the record. Its images are a grid: a column per photograph, a
   row per flow, the photographs' row last, a waiting tile per image to come.
   h j k l or the arrows move; ↵ opens the viewer over the row, unless a button or
   link such as Stop has the focus and answers it. `toggle` is the key that opens it. */
const props = defineProps<{ toggle: Key }>()
const router = useRouter()
const drawer = useDrawerStore()
const live = useLiveStore()
const { shown: target, record, photographs: named } = storeToRefs(drawer)
const { jobs, billing, now } = storeToRefs(live)
const stopRefusal = ref<string | null>(null)
const dialog = ref<HTMLDialogElement | null>(null)

const batch = computed(() => target.value?.batch ?? '')
/* The render slot's session, while it is the shown one. */
const slot = computed(() => {
  const held = jobs.value.render
  return held?.batch === target.value?.batch && held?.session?.id === target.value?.id
    ? held
    : null
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
const listed = computed(() => {
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

/* Each column's photograph: its source's, by name, once the hub is read; else the
   run's own, whole, at the address of any flow that plans or landed it. */
const photographs = computed(() =>
  layout.value.digests.map((digest, column) => {
    const name = named.value[digest]
    if (name)
      return {
        src: sourceAt(batch.value, name),
        thumb: sourceThumbAt(batch.value, name),
        name,
      }
    const row = layout.value.cells.findIndex(
      (cells) => cells[column].images.length > 0 || cells[column].waiting > 0,
    )
    const src = photoUrl({ batch: batch.value, digest, flow: layout.value.flows[row] })
    return { src, thumb: src, name: digest }
  }),
)

const { viewing, viewed, open: openViewer } = useSessionViewer(
  () => target.value,
  () => layout.value,
  () => photographs.value,
)

/* Open the viewer over `at`'s row, on the cell's `index`th image. */
function view(at: Focus, index = 0): void {
  focus.value = at
  openViewer(at, index)
}

function place(at: Focus): void {
  focus.value = at
  void nextTick(() =>
    dialog.value?.querySelector<HTMLElement>(`[data-cell="${at.row}-${at.column}"]`)?.focus(),
  )
}

const go = (move: Move) => () => place(moved(lastColumns(layout.value), focus.value, move))

function renders(): void {
  drawer.close()
  void router.push({ name: 'renders', params: { batch: batch.value } })
}

useKeys('overlay', [
  { id: 'left', keys: plain('KeyH', 'ArrowLeft'), label: 'previous photograph', run: go('column-') },
  { id: 'right', keys: plain('KeyL', 'ArrowRight'), label: 'next photograph', run: go('column+') },
  { id: 'down', keys: plain('KeyJ', 'ArrowDown'), label: 'next row', run: go('row+') },
  { id: 'up', keys: plain('KeyK', 'ArrowUp'), label: 'previous row', run: go('row-') },
  {
    id: 'open',
    keys: plain('Enter'),
    label: 'the viewer',
    run: () => view(focus.value),
    when: () => layout.value.digests.length > 0 && !isControl(document.activeElement),
  },
  {
    id: 'renders',
    keys: [shifted('KeyI')],
    label: 'renders',
    run: renders,
    when: () => target.value !== null,
  },
  {
    id: 'close',
    keys: [...plain('Escape'), props.toggle],
    label: 'close',
    run: drawer.close,
    inField: true,
  },
])

useHeldFocus(dialog, drawer.close)

/* The first render takes the focus once the record is read, and holds the tab stop. */
watch(
  () => record.value !== null,
  () => {
    if (record.value) place(first(layout.value, record.value))
  },
)

async function stop(): Promise<void> {
  try {
    await live.stop('render')
  } catch (reason) {
    stopRefusal.value = (reason as Error).message
  }
}

onMounted(() => {
  dialog.value?.showModal()
  if (record.value) place(first(layout.value, record.value))
})
</script>

<template>
  <dialog ref="dialog" class="drawer" aria-label="Render session" data-drawer @cancel.prevent>
    <section v-if="record || slot" class="session" :data-session="target?.id">
      <span class="section-label">
        Render session · {{ batch }} · {{ of }} {{ noun(of, 'image') }}
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
        <li v-for="step in listed" :key="step.name" :data-step="step.name" :data-state="step.state">
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
              v-for="(one, index) in cell.images"
              :key="`${one.version}/${one.seed}`"
              class="session__tile session__tile--done"
              type="button"
              tabindex="-1"
              :aria-label="`view ${one.flow} v${one.version} seed ${one.seed}`"
              data-session-image
              @click.stop="view({ row: at, column }, index)"
            >
              <img :src="thumbAt({ batch, ...one })" alt="" />
            </button>
            <span
              v-for="index in cell.waiting"
              :key="`waiting-${index}`"
              class="session__tile"
              data-waiting
            />
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
            :aria-label="`view the photograph ${photographs[column].name}`"
            data-session-source
            @click="view({ row: layout.flows.length, column })"
          >
            <img :src="photographs[column].thumb" alt="" loading="lazy" />
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
          <RouterLink
            class="btn btn-primary"
            data-renders
            :to="{ name: 'renders', params: { batch } }"
            @click="drawer.close"
            >View in Renders<KeyHint command="renders" /></RouterLink
          >
        </template>
      </footer>
    </section>
    <p v-else class="drawer__empty" data-drawer-empty>No render running.</p>
    <ImageViewer
      v-if="viewing && viewed.length"
      :images="viewed"
      :start="viewing.start"
      @close="viewing = null"
    />
  </dialog>
</template>
