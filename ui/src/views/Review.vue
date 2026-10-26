<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import {
  cancelApproval,
  discardDraft,
  fieldCandidates,
  imageAt,
  photoUrl as photoAt,
} from '../api'
import ApproveBar from '../components/ApproveBar.vue'
import BatchRail from '../components/BatchRail.vue'
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
import { useQueue } from '../composables/useQueue'
import { useSheet } from '../composables/useSheet'
import { clamp } from '../grid'
import { nextPane, type Pane, paneKeys } from '../panes'
import { type Command, modded, plain, shifted, useKeyStore } from '../stores/keys'
import type { FieldCandidates } from '../types'

/* Review: one batch in one flow, the run in the URL. It shows the loading state
   or the review layout; the viewer layers over either. The router keys
   this view by batch and flow, so a new digest is a new sheet in the same view.

   It owns the global keyboard model -- the bindings that cross components, so
   no component ends up owning two of them -- and the chip selection for the
   focused field, because the chips render in `FieldRow` while the keys that
   move between them are read by `TagInput`. */
const props = defineProps<{ batch: string; digest: string; flow: string }>()
const router = useRouter()
const batch = useQueue(props.batch, props.flow, () => props.digest)
const failure = ref<string | null>(null)
/* A refusal reading the sheet again after an approval, a cancel or a discard,
   or of the cancel or the discard itself: the bar says what could not be done. */
const refused = ref<string | null>(null)
const cancelling = ref(false)
const sheet = useSheet({ batch: props.batch, flow: props.flow })
const approval = useApproval()
const current = computed(() => props.digest)
const photoUrl = (digest: string) => photoAt({ batch: props.batch, digest, flow: props.flow })
const schema = computed(() => sheet.detail.value?.schema ?? [])
/* A draft copied from an approval, while it is still a draft: the approval's
   fields mark what changed, and its image sits beside the photograph (J5·4). */
const revision = computed(() =>
  sheet.readonly.value ? null : (sheet.detail.value?.revision ?? null),
)
/* A draft drafted from another flow's approval: its own sheet's fields mark
   what that approval changed. */
const drafted = computed(() => sheet.detail.value?.drafted ?? null)
const revised = computed(() => {
  const held = revision.value
  if (!held?.seed) return null
  return { src: imageAt({ ...props, version: held.version, seed: held.seed }), seed: held.seed }
})
const vocabulary = computed(() => sheet.detail.value?.vocabulary ?? 0)

/* The URL is the state: choosing another sheet is a navigation. */
function select(digest: string): void {
  if (digest !== props.digest)
    void router.push({ name: 'review', params: { ...props, digest } })
}

/* The next flow holding unapproved sheets, opened on its first. */
function nextFlow(): void {
  const next = batch.others.value[0]
  if (next)
    void router.push({ name: 'review', params: { ...props, digest: next.first, flow: next.flow } })
}

function stepBatch(direction: -1 | 1): void {
  const inputs = batch.inputs.value
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
type Lens = 'photo' | 'render' | 'pair' | 'cheatsheet'

const lens = ref<Lens | null>(null)
/* Where the focus was when a lens opened, a field included: closing gives it back. */
let returnTo: HTMLElement | null = null
const candidates = ref<FieldCandidates | null>(null)
/* True while a lens is up, by construction rather than by remembering to set two
   flags together. `TagInput` reads it and yields Escape and the arrows, so `Esc`
   closes the lens rather than clearing a fragment behind it and `←`/`→` do not
   fire twice — once for chip selection and once for the batch. */
const suspended = computed(() => lens.value !== null)
const selectedChip = ref<number | null>(null)

/* What the viewer shows: the rail's photographs from the open one, the render
   being revised alone, or the photograph and the render side by side. */
const photos = computed(() =>
  batch.inputs.value.map((input) => ({
    src: photoUrl(input.id),
    name: input.name,
    width: input.width,
    height: input.height,
  })),
)
const opened = computed(() =>
  Math.max(
    batch.inputs.value.findIndex((input) => input.id === current.value),
    0,
  ),
)
const viewed = computed(() => {
  if (lens.value === 'photo') return { images: photos.value, start: opened.value }
  if (!revised.value) return null
  const render = { src: revised.value.src, name: `render · seed ${revised.value.seed}` }
  if (lens.value === 'render') return { images: [render], start: 0 }
  const photo = photos.value[opened.value]
  if (lens.value === 'pair' && photo) return { images: [photo, render], start: 0 }
  return null
})

const clock = (at: number | null) =>
  at === null ? null : new Date(at * 1000).toLocaleTimeString('en-GB', { hour12: false })

/* The draft's time to the minute. It is rewritten every few seconds while the
   operator types, and a seconds field that ticks under the eye is noise; the
   approved time keeps its seconds, because it is written once. */
const minute = (at: number | null) =>
  at === null
    ? null
    : new Date(at * 1000).toLocaleTimeString('en-GB', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
      })

/* When the sheet was approved: in this sitting, else as the server read it. */
const approvedAt = computed(() => clock(approval.at.value ?? sheet.detail.value?.approved_at ?? null))

/* Every refusal the page meets, in the approve bar. */
const refusal = computed(
  () =>
    approval.refusal.value ?? sheet.refusal.value ?? refused.value,
)

/* `③ sheet — approved` once it is, which is also when the fields go read-only.
   The reading is taken from disk rather than from anything held here. It is NOT
   "has no draft": `review --new-version` writes a draft beside the approved
   artifact, and that input is re-opened -- editable, and carrying a correction
   the tagger did not write. */
const kicker = computed(() => {
  if (drafted.value) return `from ${drafted.value.flow} v${drafted.value.approval}`
  // No approved artifact is the tagger's draft, whether or not the payload has
  // arrived -- `readonly` defaults to true while `detail` is null, so testing
  // it first would call an unloaded sheet approved.
  if (!sheet.detail.value?.approved) return 'draft from the tagger'
  if (sheet.readonly.value) return approvedAt.value ? `approved ${approvedAt.value}` : 'approved'
  const held = revision.value
  if (held?.seed) return `revision of render ${held.seed}`
  return held ? `revision of v${held.version}` : 're-opened'
})

/* Read the batch and the open sheet again, staying on it; a refusal shows in
   the approve bar. */
async function reread(id: string): Promise<void> {
  refused.value = null
  const [read] = await Promise.allSettled([batch.load(), sheet.open(id)])
  focused.value = null
  selectedChip.value = null
  if (read.status === 'rejected') refused.value = (read.reason as Error).message
}

/* Delete this draft, as `review --discard` does, and stay on the sheet. A save
   still in flight lands first, so the discard states the draft it moved to
   rather than racing it. */
async function discard(): Promise<void> {
  refused.value = null
  if (!(await sheet.flush())) return
  try {
    await discardDraft(
      { batch: props.batch, digest: current.value, flow: props.flow },
      sheet.saved.value,
    )
  } catch (reason) {
    refused.value = (reason as Error).message
    return
  }
  await reread(current.value)
}

async function approve(): Promise<void> {
  const id = current.value
  if (!id || sheet.readonly.value) return
  // Awaited, not merely started: the debounced write has to be ON DISK before
  // the approve `POST` goes out, or the artifact is built from the previous
  // draft and the last correction is unlinked along with it.
  //
  // **And read, not merely awaited.** A refused `PUT` used to mean a network
  // error and nothing else; it now means 409 too -- an approved input, or a
  // `saved` the disk has moved past -- so waiting for an answer nobody looks at
  // would approve the draft as of the last write that *did* land and discard
  // everything typed after it, behind a banner the operator has no reason to
  // read as "your approval is about to be wrong". `flush()` leaves the refusal
  // in the approve bar; stopping here is what makes it true.
  if (!(await sheet.flush())) return
  const place = { batch: props.batch, digest: id, flow: props.flow }
  if (!(await approval.approve(place, sheet.saved.value))) return
  // Approving is an act, not a navigation: the sheet stays, read-only.
  await reread(id)
}

/* Take the approval back, as `approve --cancel` does, and stay on the sheet:
   editable again, or, for a copy, on the draft open above what lies beneath,
   else the approval beneath, read-only. */
async function cancelApprove(): Promise<void> {
  const id = current.value
  if (!id) return
  cancelling.value = true
  try {
    await cancelApproval({ batch: props.batch, digest: id, flow: props.flow })
  } catch (reason) {
    refused.value = (reason as Error).message
    return
  } finally {
    cancelling.value = false
  }
  approval.forget()
  await reread(id)
}

/* The rail already knows every input's dimensions, so the source column draws
   its frame at the right aspect ratio while the payload is still in flight --
   which is what keeps the photograph from reflowing the column when it lands. */
const showing = computed(
  () =>
    sheet.detail.value ??
    batch.inputs.value.find((input) => input.id === current.value) ??
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
  batch.markEdited(current.value)
}

function back(field: string): void {
  const count = chips(field)
  if (count === 0) return
  const at = selectedChip.value ?? count - 1
  sheet.remove(field, at)
  selectedChip.value = null
  batch.markEdited(current.value)
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

/* `⌃P`: the photograph, on a revision the pair; in the pair, the photograph alone
   and back. */
function photograph(): void {
  if (lens.value === 'pair') lens.value = 'photo'
  else if (lens.value === 'photo' && revised.value) lens.value = 'pair'
  else if (lens.value === 'photo') closeLens()
  else void openLens(revised.value ? 'pair' : 'photo')
}

const photographKey: Command = {
  id: 'photograph',
  keys: [{ code: 'KeyP', ctrl: true }],
  label: 'the photograph, on a revision side by side',
  run: photograph,
  inField: true,
  when: () => sheet.detail.value !== null,
}

const scrollSource = (direction: -1 | 1) => source.value?.scrollBy({ top: direction * 120 })

/* ④'s stops, the count then each slot, walked from the one focused. */
function moveRenders(direction: -1 | 1): void {
  const stops = [
    ...document.querySelectorAll<HTMLElement>(
      '.renders-block [data-renders-count], .renders-block [data-slot]',
    ),
  ]
  const at = stops.findIndex((one) => one === document.activeElement)
  stops[clamp(at + direction, stops.length - 1)]?.focus()
}

/* A slot takes digits alone, so `j` `k` walk ④ from inside one. */
const inSlot = () => document.activeElement?.matches('[data-slot]') ?? false

/* `j` `k` or ↓ ↑: the rail changes the input, the source pane scrolls, the
   sheet walks its rows from the field last left, and ④ its stops. */
function vertical(direction: -1 | 1): () => void {
  return () => {
    const here = paneNow()
    if (here === 'rail') stepBatch(direction)
    else if (here === 'source') scrollSource(direction)
    else if (here === 'sheet') moveRow(direction)
    else moveRenders(direction)
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
    run: () => stepBatch(1),
  },
  {
    id: 'previous-sheet',
    keys: [shifted('KeyK'), shifted('ArrowUp')],
    label: 'previous sheet',
    run: () => stepBatch(-1),
  },
  {
    id: 'next-flow',
    keys: [shifted('KeyF')],
    label: 'the next flow',
    run: nextFlow,
    when: () => batch.others.value.length > 0,
  },
  ...paneKeys(useKeyStore().mac, movePane, moveRow),
  { id: 'down', keys: plain('KeyJ', 'ArrowDown'), label: 'down', run: vertical(1) },
  { id: 'up', keys: plain('KeyK', 'ArrowUp'), label: 'up', run: vertical(-1) },
  {
    id: 'slot-down',
    keys: plain('KeyJ', 'ArrowDown'),
    label: 'next slot',
    run: () => moveRenders(1),
    inField: true,
    when: inSlot,
  },
  {
    id: 'slot-up',
    keys: plain('KeyK', 'ArrowUp'),
    label: 'previous slot',
    run: () => moveRenders(-1),
    inField: true,
    when: inSlot,
  },
  {
    id: 'scroll-down',
    keys: [{ code: 'KeyE', ctrl: true }],
    label: 'scroll the photograph',
    run: () => scrollSource(1),
  },
  {
    id: 'scroll-up',
    keys: [{ code: 'KeyY', ctrl: true }],
    label: 'scroll back',
    run: () => scrollSource(-1),
  },
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
  const [read] = await Promise.allSettled([batch.load(), sheet.open(current.value)])
  if (read.status === 'rejected') {
    failure.value = (read.reason as Error).message
    return
  }
  // The rail first: it is where the operator decides what they are looking at.
  await nextTick()
  enter('rail')
})

onUnmounted(() => window.removeEventListener('beforeunload', onLeave))

watch(current, (id) => {
  if (!id) return
  // The pending write belongs to the input being left, not the one arriving.
  // Not awaited: `flush()` takes the edit and its id before `open()` moves
  // `current`, and the save states the receipt of that input's own last save.
  void sheet.flush()
  focused.value = null
  selectedChip.value = null
  approval.forget()
  refused.value = null
  lastField.value = null
  void sheet.open(id).then(() => enter(paneNow()))
})
</script>

<template>
  <RefusalPage v-if="failure" :refusal="failure" />
  <div v-else class="review">
    <LoadingSkeleton
      v-if="batch.loading.value || sheet.loading.value"
      class="review__reading"
      :reading="batch.loading.value ? null : current"
      :vocabulary="vocabulary"
    />
    <div v-if="batch.info.value" class="work" @focusin="remember">
      <BatchRail
        :flow="props.flow"
        :inputs="batch.inputs.value"
        :others="batch.others.value"
        :approved="batch.approved.value"
        :current="current"
        :edited="batch.edited.value"
        :photo-url="photoUrl"
        :loading="batch.loading.value"
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
        @remove="(field, index) => (sheet.remove(field, index), batch.markEdited(current))"
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
      :commands="[photographKey]"
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
