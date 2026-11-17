<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import { fieldCandidates, imageAt, photoUrl as photoAt, sourceCopyUrl } from '../api'
import ApproveBar from '../components/ApproveBar.vue'
import CollectionRail from '../components/CollectionRail.vue'
import CheatsheetOverlay from '../components/CheatsheetOverlay.vue'
import ImageViewer from '../components/ImageViewer.vue'
import LoadingSkeleton from '../components/LoadingSkeleton.vue'
import RefusalPage from '../components/RefusalPage.vue'
import RendersBlock from '../components/RendersBlock.vue'
import SheetForm from '../components/SheetForm.vue'
import SourcePanel from '../components/SourcePanel.vue'
import TagInput from '../components/TagInput.vue'
import { useApproval } from '../composables/useApproval'
import { useKeys } from '../composables/useKeys'
import { chooses, useQueue } from '../composables/useQueue'
import { useReviewActions } from '../composables/useReviewActions'
import { useSheet } from '../composables/useSheet'
import type { Move } from '../grid'
import { clock, kickerOf, minute } from '../kicker'
import { type Lens, photographStep, viewedOf } from '../lens'
import { nextPane, type Pane, paneKeys } from '../panes'
import { nearest, stepFour } from '../slots'
import { type Command, modded, plain, shifted, useKeyStore } from '../stores/keys'
import type { FieldCandidates } from '../types'

/* Review: one collection in one flow, the run in the URL. It shows the loading state
   or the review layout; the viewer layers over either. The router keys
   this view by collection and flow, so a new digest is a new sheet in the same view.

   It owns the global keyboard model -- the bindings that cross components, so
   no component ends up owning two of them -- and the chip selection for the
   focused field, because the chips render in `FieldRow` while the keys that
   move between them are read by `TagInput`. */
const props = defineProps<{ collection: string; digest: string; flow: string }>()
const router = useRouter()
const mac = useKeyStore().mac
const queue = useQueue(props.collection, props.flow, () => props.digest)
const failure = ref<string | null>(null)
const sheet = useSheet({ collection: props.collection, flow: props.flow })
const approval = useApproval()
const current = computed(() => props.digest)
const photoUrl = (digest: string) => photoAt({ collection: props.collection, digest, flow: props.flow })
const schema = computed(() => sheet.detail.value?.schema ?? [])
/* A draft copied from an approval, and once approved too: the approval's fields
   mark what changed, and its image sits beside the photograph (J5·4). */
const revision = computed(() => sheet.detail.value?.revision ?? null)
/* A draft drafted from another flow's approval, and once approved too: its own
   sheet's fields mark what that approval changed, read-only once approved. */
const drafted = computed(() => sheet.detail.value?.drafted ?? null)
/* The image a draft came from: a revision's, else a drafted draft's source copy. */
const revised = computed(() => {
  const held = revision.value
  if (held?.seed)
    return { src: imageAt({ ...props, version: held.version, seed: held.seed }), seed: held.seed }
  if (!drafted.value) return null
  return { src: sourceCopyUrl(props, drafted.value.version), seed: null }
})
const vocabulary = computed(() => sheet.detail.value?.vocabulary ?? 0)

/* The URL is the state: choosing another sheet is a navigation. */
function select(digest: string): void {
  if (digest !== props.digest)
    void router.push({ name: 'review', params: { ...props, digest } })
}

function stepCollection(direction: -1 | 1): void {
  const inputs = queue.inputs.value
  const at = inputs.findIndex((i) => i.id === props.digest)
  if (at < 0 || inputs.length === 0) return
  select(inputs[(at + direction + inputs.length) % inputs.length].id)
}

/* The panes are `panes.ts`'s. Inside a pane `j` `k` or the vertical arrows do
   that pane's own thing — change the input, scroll the caption, walk the rows. */
const focused = ref<string | null>(null)
/* Where the sheet was left. `focused` is cleared on blur, because the row
   highlight must not survive the operator leaving it -- but coming back from
   the caption should land on the field they went to read about, not on the top
   of the sheet. Cleared when the input changes. */
const lastField = ref<string | null>(null)
let pane: Pane = 'rail'
const source = ref<HTMLElement | null>(null)
/* **One state, not two booleans.** Which lens is up, or none. Opening and
   closing are the only two transitions, and each of them owns the focus
   round-trip — so a new way to open one cannot skip the blur, which is exactly
   what a `overlay = true` on a click handler did while the flags were separate.

   `candidates` is fetched once per sitting and then held: the table does not
   move while a surface is up. */
const lens = ref<Lens | null>(null)
/* Where the focus was when a lens opened, a field included: closing gives it back. */
let returnTo: HTMLElement | null = null
const candidates = ref<FieldCandidates | null>(null)
/* True while a lens is up, by construction rather than by remembering to set two
   flags together. `TagInput` reads it and yields Escape and the arrows, so `Esc`
   closes the lens rather than clearing a fragment behind it and `←`/`→` do not
   fire twice — once for chip selection and once for the queue. */
const suspended = computed(() => lens.value !== null)
const selectedChip = ref<number | null>(null)

/* What the viewer shows: the rail's photographs from the open one, the image a
   draft came from alone, or the photograph and that image side by side. */
const photos = computed(() =>
  queue.inputs.value.map((input) => ({
    src: photoUrl(input.id),
    name: input.name,
    width: input.width,
    height: input.height,
  })),
)
const opened = computed(() =>
  Math.max(
    queue.inputs.value.findIndex((input) => input.id === current.value),
    0,
  ),
)
const viewed = computed(() => viewedOf(lens.value, photos.value, opened.value, revised.value))

/* When the sheet was approved: in this sitting, else as the server read it. */
const approvedAt = computed(() => clock(approval.at.value ?? sheet.detail.value?.approved_at ?? null))

const kicker = computed(() =>
  kickerOf({
    drafted: drafted.value !== null,
    approved: Boolean(sheet.detail.value?.approved),
    readonly: sheet.readonly.value,
    approvedAt: approvedAt.value,
    revision: revision.value,
  }),
)

/* The rail already knows every input's dimensions, so the source column draws
   its frame at the right aspect ratio while the payload is still in flight --
   which is what keeps the photograph from reflowing the column when it lands. */
const showing = computed(
  () =>
    sheet.detail.value ??
    queue.inputs.value.find((input) => input.id === current.value) ??
    null,
)

const chips = (field: string | null) => (field ? (sheet.fields.value[field] ?? []).length : 0)

function focus(field: string): void {
  focused.value = field
  lastField.value = field
  selectedChip.value = null
}

function step(direction: -1 | 1): void {
  const count = chips(focused.value)
  if (count === 0) return
  const at = selectedChip.value
  if (at === null) selectedChip.value = direction === -1 ? count - 1 : 0
  else selectedChip.value = (at + direction + count) % count
}

/* The pane an element sits in, or null. ④ sits inside the sheet's form. */
function paneOf(element: Element | null): Pane | null {
  if (!element) return null
  if (element.closest('.rail')) return 'rail'
  if (element.closest('.source')) return 'source'
  if (element.closest('.renders-block')) return 'renders'
  if (element.closest('.form')) return 'sheet'
  return null
}

/* Which pane holds the focus, read from the document rather than remembered:
   the operator can click into any of them, and a remembered answer would send
   the next `l` from somewhere they are not. Out of every pane, such as after
   `Esc` leaves a field, it is the pane last entered. */
function paneNow(): Pane {
  return paneOf(document.activeElement) ?? pane
}

function remember(event: FocusEvent): void {
  pane = paneOf(event.target as Element | null) ?? pane
}

/* The element a pane gives the focus to, or null when it holds none. */
function entry(next: Pane): HTMLElement | null {
  if (next === 'rail') return document.querySelector<HTMLElement>('.rail__card--current')
  if (next === 'source') return document.querySelector<HTMLElement>('.source')
  if (next === 'renders') {
    const block = document.querySelector<HTMLElement>('.renders-block')
    return block?.querySelector<HTMLElement>('button:not(:disabled), input') ?? block
  }
  const field = lastField.value ?? schema.value[0]
  return field
    ? document.querySelector<HTMLInputElement>(`input.fragment[data-field="${field}"]`)
    : null
}

/* A pane with nothing to focus still takes the next key: the focus leaves the
   pane it was in, and `pane` answers for it. */
function enter(next: Pane): void {
  pane = next
  const target = entry(next)
  if (target) target.focus()
  else if (document.activeElement instanceof HTMLElement) document.activeElement.blur()
}

function movePane(direction: -1 | 1): void {
  enter(nextPane(paneNow(), direction))
}

/* Walk the sheet with the vertical keys, clamped at both ends. A 16-row list
   that jumped from `count` to `background` on one ↑ would lose the operator's
   place rather than move it, which is the same reason the dropdown overlays. */
function moveRow(direction: -1 | 1): void {
  const order = schema.value
  const from = focused.value ?? lastField.value
  const at = from ? order.indexOf(from) : -1
  if (at < 0) return
  const next = order[Math.min(Math.max(at + direction, 0), order.length - 1)]
  document
    .querySelector<HTMLInputElement>(`input.fragment[data-field="${next}"]`)
    ?.focus()
}

function commit(field: string, tag: string): void {
  sheet.commit(field, tag, selectedChip.value)
  selectedChip.value = null
  queue.markEdited(current.value)
}

function back(field: string): void {
  const count = chips(field)
  if (count === 0) return
  const at = selectedChip.value ?? count - 1
  sheet.remove(field, at)
  selectedChip.value = null
  queue.markEdited(current.value)
}

/* Open a lens from wherever the focus is. `blur()` rather than a flag: the field
   must stop receiving keys, and the lens's own input takes the focus on mount.
   The fragment survives untouched because `TagInput` stays mounted behind the
   lens — nothing is copied out and copied back, so nothing can come back
   different. Every path that opens a lens goes through here, including the click
   on the photograph. */
async function openLens(which: Lens): Promise<void> {
  const held = document.activeElement
  if (lens.value === null && held instanceof HTMLElement && held !== document.body) returnTo = held
  if (which === 'cheatsheet' && !candidates.value) {
    candidates.value = await fieldCandidates(props.flow)
  }
  if (document.activeElement instanceof HTMLElement) document.activeElement.blur()
  lens.value = which
}

/* Give the focus back where the lens found it; with none, `enter('sheet')`
   focuses `lastField`, what the operator was typing into. */
function closeLens(): void {
  lens.value = null
  const back = returnTo
  returnTo = null
  void nextTick(() => (back?.isConnected ? back.focus() : enter('sheet')))
}

function toggleLens(which: Lens): void {
  if (lens.value === which) closeLens()
  else void openLens(which)
}

function photograph(): void {
  const to = photographStep(lens.value, revised.value !== null)
  if (to === 'close') closeLens()
  else if (lens.value === 'pair' || lens.value === 'photo') lens.value = to
  else void openLens(to)
}

const photographKey: Command = {
  id: 'photograph',
  keys: [{ code: 'KeyP', ctrl: true }],
  label: 'the photograph, on a revision or a draft from an image side by side',
  run: photograph,
  inField: true,
  when: () => sheet.detail.value !== null,
}
/* What the viewer adds to its own keys: `⌃P` reaches into it. */
const viewerKeys = [photographKey]

const scrollSource = (direction: -1 | 1) => source.value?.scrollBy({ top: direction * 120 })

/* ④ as a grid the keys step, as on every grid: the count's `−` `+` a row, then a row per slot. */
function fourStops(): HTMLElement[][] {
  const block = document.querySelector('.renders-block')
  if (!block) return []
  const count = [...block.querySelectorAll<HTMLElement>('[data-renders-step]')]
  const slots = [...block.querySelectorAll<HTMLElement>('[data-slot]')].map((one) => [one])
  return count.length > 0 ? [count, ...slots] : slots
}

/* The column a row move keeps, the one `h` `l` last took. */
let fourColumn = 0

function moveRenders(move: Move): void {
  const stops = fourStops()
  const enabled = stops.map((one) => one.map((stop) => !stop.matches(':disabled')))
  const active = document.activeElement
  const row = stops.findIndex((one) => one.some((stop) => stop === active))
  if (row < 0) {
    stops[0]?.[nearest(enabled[0] ?? [], 0)]?.focus()
    return
  }
  const at = { row, column: stops[row].findIndex((stop) => stop === active) }
  const to = stepFour(enabled, at, move, fourColumn)
  fourColumn = to.kept
  stops[to.focus.row]?.[to.focus.column]?.focus()
}

/* A slot takes digits alone, so `j` `k` walk ④ from inside one. */
const inSlot = () => document.activeElement?.matches('[data-slot]') ?? false

/* `j` `k` or ↓ ↑: the rail changes the input, the source pane scrolls, the
   sheet walks its rows from the field last left, and ④ its stops. */
function vertical(direction: -1 | 1): () => void {
  return () => {
    const here = paneNow()
    if (here === 'rail') stepCollection(direction)
    else if (here === 'source') scrollSource(direction)
    else if (here === 'sheet') moveRow(direction)
    else moveRenders(direction > 0 ? 'row+' : 'row-')
  }
}

/* The keys that cross components, so no component owns two of them (D25). Mod+K,
   Mod+↵, Mod+Z and ⌃P reach into a field: they are what the operator presses mid-edit. */
useKeys('screen', [
  {
    id: 'approve',
    keys: [modded('Enter')],
    label: 'approve',
    run: () => void approve(),
    inField: true,
  },
  { id: 'undo', keys: [modded('KeyZ')], label: 'undo', run: () => sheet.undo(), inField: true },
  {
    id: 'redo',
    keys: [{ code: 'KeyZ', shift: true, mod: true }],
    label: 'redo',
    run: () => sheet.redo(),
    inField: true,
  },
  {
    id: 'cheatsheet',
    keys: [modded('KeyK')],
    label: 'the tag cheatsheet',
    run: () => toggleLens('cheatsheet'),
    inField: true,
  },
  {
    id: 'next-sheet',
    keys: [shifted('KeyJ'), shifted('ArrowDown')],
    label: 'next sheet',
    run: () => stepCollection(1),
  },
  {
    id: 'previous-sheet',
    keys: [shifted('KeyK'), shifted('ArrowUp')],
    label: 'previous sheet',
    run: () => stepCollection(-1),
  },
  {
    id: 'flows',
    keys: plain('Escape'),
    label: 'the flows waiting',
    run: () => void router.push({ name: 'review-head', params: { collection: props.collection } }),
    when: () => queue.info.value !== null && chooses(queue.info.value),
  },
  ...paneKeys(mac, movePane, moveRow),
  { id: 'down', keys: plain('KeyJ', 'ArrowDown'), label: 'down', run: vertical(1) },
  { id: 'up', keys: plain('KeyK', 'ArrowUp'), label: 'up', run: vertical(-1) },
  {
    id: 'slot-down',
    keys: plain('KeyJ', 'ArrowDown'),
    label: 'next slot',
    run: () => moveRenders('row+'),
    inField: true,
    when: inSlot,
  },
  {
    id: 'slot-up',
    keys: plain('KeyK', 'ArrowUp'),
    label: 'previous slot',
    run: () => moveRenders('row-'),
    inField: true,
    when: inSlot,
  },
  ...(
    [
      ['four-left', plain('KeyH', 'ArrowLeft'), 'column-'],
      ['four-right', plain('KeyL', 'ArrowRight'), 'column+'],
    ] as const
  ).map(([id, keys, to]) => ({
    id,
    keys: [...keys],
    label: to === 'column-' ? 'left in ④' : 'right in ④',
    run: () => moveRenders(to),
    when: () => mac && paneNow() === 'renders',
  })),
  photographKey,
])

// The draft is flushed as the tab goes; the PUT is kept alive past the page. An
// edit still waiting for an earlier save cannot be sent before the page goes, so
// the browser asks the operator to stay rather than lose it unsaid.
const onLeave = (event: BeforeUnloadEvent) => {
  if (!sheet.leave()) return
  event.preventDefault()
  event.returnValue = true
}

// Leaving for another screen flushes too; the draft is the operator's work.
onBeforeRouteLeave(async () => {
  await sheet.flush()
})

onMounted(async () => {
  window.addEventListener('beforeunload', onLeave)
  // Independent reads: the sheet needs only the route's digest.
  const [read] = await Promise.allSettled([queue.load(), sheet.open(current.value)])
  if (read.status === 'rejected') {
    failure.value = (read.reason as Error).message
    return
  }
  // The rail first: it is where the operator decides what they are looking at.
  await nextTick()
  enter('rail')
})

onUnmounted(() => window.removeEventListener('beforeunload', onLeave))

const { approve, cancelApprove, cancelling, discard, forget, refusal } = useReviewActions({
  collection: () => props.collection,
  flow: () => props.flow,
  digest: () => current.value,
  sheet,
  queue,
  approval,
  settled: () => {
    focused.value = null
    selectedChip.value = null
  },
})

watch(current, (id) => {
  if (!id) return
  // The pending write belongs to the input being left, not the one arriving.
  // Not awaited: `flush()` takes the edit and its id before `open()` moves
  // `current`, and the save states the receipt of that input's own last save.
  void sheet.flush()
  focused.value = null
  selectedChip.value = null
  forget()
  lastField.value = null
  void sheet.open(id).then(() => enter(paneNow()))
})
</script>

<template>
  <RefusalPage v-if="failure" :refusal="failure" />
  <div v-else class="review">
    <LoadingSkeleton
      v-if="queue.loading.value || sheet.loading.value"
      class="review__reading"
      :reading="queue.loading.value ? null : current"
      :vocabulary="vocabulary"
    />
    <div v-if="queue.info.value" class="work" @focusin="remember">
      <CollectionRail
        :flow="props.flow"
        :inputs="queue.inputs.value"
        :others="queue.others.value"
        :approved="queue.approved.value"
        :current="current"
        :edited="queue.edited.value"
        :photo-url="photoUrl"
        :loading="queue.loading.value"
        @select="select"
      />

      <SourcePanel
        v-if="showing"
        ref="source"
        :id="showing.id"
        :width="showing.width"
        :height="showing.height"
        :photo="photoUrl(showing.id)"
        :caption="sheet.detail.value?.caption ?? null"
        :caption-command="sheet.detail.value?.caption_command ?? null"
        :wd14="sheet.detail.value?.wd14 ?? null"
        :tags="sheet.detail.value?.tags ?? null"
        :loading="sheet.loading.value"
        :revised="revised"
        @open="openLens('photo')"
        @render="openLens('render')"
        @pair="openLens('pair')"
      />
      <SheetForm
        :schema="schema"
        :fields="sheet.fields.value"
        :budget="sheet.budget.value"
        :readonly="sheet.readonly.value"
        :focused="focused"
        :selected="selectedChip"
        :loading="sheet.loading.value"
        :kicker="kicker"
        :saving="sheet.saving.value"
        :saved="sheet.readonly.value ? null : minute(sheet.saved.value)"
        :previous="revision?.fields ?? drafted?.fields ?? null"
        @remove="(field, index) => (sheet.remove(field, index), queue.markEdited(current))"
      >
        <template #editor="{ field }">
          <TagInput
            v-if="!sheet.readonly.value && !sheet.loading.value"
            :vocabulary="vocabulary"
            :field="field"
            :focused="focused === field"
            :suspended="suspended"
            :chips="chips(field)"
            :selected="focused === field ? selectedChip : null"
            @focus="focus(field)"
            @blur="focused === field && (focused = null)"
            @commit="(tag) => commit(field, tag)"
            @back="back(field)"
            @step="step"
            @row="moveRow"
          />
        </template>
        <template #aside>
          <RendersBlock
            v-if="!sheet.loading.value"
            :key="current"
            :renders="sheet.renders.value"
            :readonly="sheet.readonly.value"
            @change="sheet.setRenders"
          />
        </template>
        <template #footer>
          <ApproveBar
            :key="current"
            :approved="sheet.readonly.value"
            :at="approvedAt"
            :approval="sheet.detail.value?.approved ?? null"
            :working="approval.working.value || cancelling"
            :refusal="refusal"
            :discardable="revision !== null || drafted !== null"
            :uncancellable="sheet.detail.value?.cancel ?? null"
            @approve="approve"
            @discard="discard"
            @cancel="cancelApprove"
          />
        </template>
      </SheetForm>
    </div>

    <ImageViewer
      v-if="viewed && viewed.images.length"
      :key="lens ?? ''"
      :images="viewed.images"
      :start="viewed.start"
      :pair="lens === 'pair'"
      :commands="viewerKeys"
      @close="closeLens"
    />

    <CheatsheetOverlay
      v-if="lens === 'cheatsheet' && candidates"
      :candidates="candidates"
      :field="lastField"
      @close="closeLens"
    />
  </div>
</template>
