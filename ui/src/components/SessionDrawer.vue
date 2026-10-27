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
import { asked, first, grid, lasted, located, outcome, stacked } from '../sessions'
import { useDrawerStore } from '../stores/drawer'
import { type Key, isControl, plain, shifted } from '../stores/keys'
import { alerting, clock, collectionsOf, useLiveStore } from '../stores/live'
import { noun } from '../words'

/* The render drawer (design spec J4·2, J4·3): the shown session, from the records
   its verb writes, over half the window. While the render slot runs it, the slot
   adds the volume steps and Stop, and the drawer is drawn from the slot until the
   verb has written the records. Its images are a grid per collection, stacked and
   each headed by its name: a column per photograph, a row per flow, the
   photographs' row last, a waiting tile per image to come. h j k l or the arrows
   move, `j` and `k` across grids too; ↵ opens the viewer over the row, unless a
   button or link such as Stop has the focus and answers it. `toggle` is the key
   that opens it. */
const props = defineProps<{ toggle: Key }>()
const router = useRouter()
const drawer = useDrawerStore()
const live = useLiveStore()
const { shown: target, records, record, photographs: named } = storeToRefs(drawer)
const { jobs, billing, now } = storeToRefs(live)
const stopRefusal = ref<string | null>(null)
const dialog = ref<HTMLDialogElement | null>(null)

const collections = computed(() => target.value?.collections ?? [])
/* The render slot's session, while it is the shown one. */
const slot = computed(() => {
  const held = jobs.value.render
  return held?.session?.id === target.value?.id &&
    held && collectionsOf(held).join('/') === collections.value.join('/')
    ? held
    : null
})
const running = computed(() => record.value?.outcome === 'running' || slot.value?.state === 'running')
const alert = computed(() => alerting(billing.value))

/* Each collection's record, in the order the session renders them. */
const held = computed(() =>
  collections.value.flatMap((one) => {
    const found = records.value?.[one]
    return found ? [{ collection: one, record: found }] : []
  }),
)
const started = computed(() => record.value?.started ?? slot.value?.session?.started ?? null)
const limit = computed(() => record.value?.limit ?? slot.value?.session?.limit ?? 0)
const of = computed(() =>
  held.value.length
    ? held.value.reduce((sum, one) => sum + asked(one.record), 0)
    : (slot.value?.session?.of ?? 0),
)
const done = computed(() => held.value.reduce((sum, one) => sum + one.record.images.length, 0))
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

/* Each collection's grid, and its photographs: its source's, by name, once its hub
   is read; else the run's own, whole, at the address of any flow that plans or
   landed it. */
const grids = computed(() =>
  held.value.map(({ collection, record: one }) => {
    const layout = grid(one)
    const photographs = layout.digests.map((digest, column) => {
      const name = named.value[collection]?.[digest]
      if (name)
        return { src: sourceAt(collection, name), thumb: sourceThumbAt(collection, name), name }
      const row = layout.cells.findIndex(
        (cells) => cells[column].images.length > 0 || cells[column].waiting > 0,
      )
      const src = photoUrl({ collection, digest, flow: layout.flows[row] })
      return { src, thumb: src, name: digest }
    })
    return { collection, record: one, layout, photographs }
  }),
)
const stack = computed(() => stacked(grids.value.map((one) => one.layout)))
/* The focus on the stacked rows: a grid's row `r` is stacked row `starts[grid] + r`. */
const focus = ref<Focus>({ row: 0, column: 0 })
const focused = (row: number, column: number) =>
  focus.value.row === row && focus.value.column === column
/* The grid the focus is in. */
const current = computed(() => grids.value[located(stack.value, focus.value.row).grid] ?? null)
const EMPTY = { digests: [], flows: [], cells: [] }

const { viewing, viewed, open: openViewer } = useSessionViewer(
  () => target.value,
  () => current.value?.layout ?? EMPTY,
  () => current.value?.photographs ?? [],
  () => current.value?.collection ?? '',
)

/* Open the viewer over stacked `at`'s row, on the cell's `index`th image. */
function view(at: Focus, index = 0): void {
  focus.value = at
  openViewer({ row: located(stack.value, at.row).row, column: at.column }, index)
}

function place(at: Focus): void {
  focus.value = at
  void nextTick(() =>
    dialog.value?.querySelector<HTMLElement>(`[data-cell="${at.row}-${at.column}"]`)?.focus(),
  )
}

/* The first grid's first landed image, else the first cell. */
function start(): Focus {
  const index = grids.value.findIndex((one) => one.record.images.length > 0)
  if (index < 0) return { row: 0, column: 0 }
  const { layout, record: one } = grids.value[index]
  const at = first(layout, one)
  return { row: stack.value.starts[index] + at.row, column: at.column }
}

const go = (move: Move) => () => place(moved(stack.value.last, focus.value, move))

function renders(): void {
  drawer.close()
  void router.push({ name: 'renders', params: { collection: current.value?.collection ?? '' } })
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
    when: () => stack.value.last.length > 0 && !isControl(document.activeElement),
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

/* The first render takes the focus once the records are read, and holds the tab stop. */
watch(
  () => record.value !== null,
  () => {
    if (record.value) place(start())
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
  if (record.value) place(start())
})
</script>

<template>
  <dialog ref="dialog" class="drawer" aria-label="Render session" data-drawer @cancel.prevent>
    <section v-if="record || slot" class="session" :data-session="target?.id">
      <span class="section-label">
        Render session · {{ collections.join(' · ') }} · {{ of }} {{ noun(of, 'image') }}
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
      <section
        v-for="(one, index) in grids"
        :key="one.collection"
        class="session__stack"
        :data-session-collection="one.collection"
      >
        <span class="section-label session__collection">{{
          one.collection
        }}</span>
        <div
          v-if="one.layout.digests.length"
          class="session__grid"
          :style="{
            gridTemplateColumns: `max-content repeat(${one.layout.digests.length}, max-content)`,
          }"
          data-session-grid
        >
          <template v-for="(flow, at) in one.layout.flows" :key="flow">
            <span class="session__flow mono">{{ flow }}</span>
            <div
              v-for="(cell, column) in one.layout.cells[at]"
              :key="one.layout.digests[column]"
              class="session__cell"
              :class="{ 'session__cell--focused': focused(stack.starts[index] + at, column) }"
              :data-cell="`${stack.starts[index] + at}-${column}`"
              :tabindex="focused(stack.starts[index] + at, column) ? 0 : -1"
              @click="focus = { row: stack.starts[index] + at, column }"
            >
              <button
                v-for="(image, nth) in cell.images"
                :key="`${image.version}/${image.seed}`"
                class="session__tile session__tile--done"
                type="button"
                tabindex="-1"
                :aria-label="`view ${image.flow} v${image.version} seed ${image.seed}`"
                data-session-image
                @click.stop="view({ row: stack.starts[index] + at, column }, nth)"
              >
                <img :src="thumbAt({ collection: one.collection, ...image })" alt="" />
              </button>
              <span
                v-for="waiting in cell.waiting"
                :key="`waiting-${waiting}`"
                class="session__tile"
                data-waiting
              />
            </div>
          </template>
          <span class="session__flow section-label">photographs</span>
          <div
            v-for="(digest, column) in one.layout.digests"
            :key="digest"
            class="session__cell"
            :class="{
              'session__cell--focused': focused(stack.starts[index] + one.layout.flows.length, column),
            }"
            :data-cell="`${stack.starts[index] + one.layout.flows.length}-${column}`"
            :tabindex="focused(stack.starts[index] + one.layout.flows.length, column) ? 0 : -1"
          >
            <button
              class="session__tile session__tile--photo"
              type="button"
              tabindex="-1"
              :aria-label="`view the photograph ${one.photographs[column].name}`"
              data-session-source
              @click="view({ row: stack.starts[index] + one.layout.flows.length, column })"
            >
              <img :src="one.photographs[column].thumb" alt="" loading="lazy" />
            </button>
          </div>
        </div>
      </section>
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
            :to="{ name: 'renders', params: { collection: current?.collection ?? collections[0] } }"
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
