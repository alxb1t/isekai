<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { fieldCandidates, inputDetail, photoUrl } from './api'
import AppHeader from './components/AppHeader.vue'
import ApproveBar from './components/ApproveBar.vue'
import BatchRail from './components/BatchRail.vue'
import CheatsheetOverlay from './components/CheatsheetOverlay.vue'
import LoadingSkeleton from './components/LoadingSkeleton.vue'
import PhotoOverlay from './components/PhotoOverlay.vue'
import RunManifest from './components/RunManifest.vue'
import SheetForm from './components/SheetForm.vue'
import SourcePanel from './components/SourcePanel.vue'
import TagInput from './components/TagInput.vue'
import { useApproval } from './composables/useApproval'
import { useBatch } from './composables/useBatch'
import { useSheet } from './composables/useSheet'
import type { ApprovedSheet, FieldCandidates } from './types'

/* The root. It shows exactly one of the loading state, the review layout, or
   the manifest; the photo overlay layers over any of them.

   It owns the global keyboard model -- the bindings that cross components, so
   no component ends up owning two of them -- and the chip selection for the
   focused field, because the chips render in `FieldRow` while the keys that
   move between them are read by `TagInput`. */
const batch = useBatch()
const sheet = useSheet()
const approval = useApproval()

/* Three panes, left to right: the rail, the photograph and its caption, the
   sheet. `Alt+←/→` moves between them and `Alt+↑/↓` moves through the batch;
   inside a pane the plain arrows do that pane's own thing — scroll the caption,
   walk the rows, change the input.

   **This overturns the design's keyboard model on one binding.** `ux-flow.md`
   gives `Alt+←/→` to the batch. The operator asked for the axes to separate:
   the rail is a vertical list, so vertical is the batch, and horizontal is the
   one movement the design had no binding for at all — getting to the caption to
   read it, and back to the field being typed. */
type Pane = 'rail' | 'source' | 'sheet'

const PANES: Pane[] = ['rail', 'source', 'sheet']

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
type Lens = 'photo' | 'cheatsheet'

const lens = ref<Lens | null>(null)
const candidates = ref<FieldCandidates | null>(null)
/* True while a lens is up, by construction rather than by remembering to set two
   flags together. `TagInput` reads it and yields Escape and the arrows, so `Esc`
   closes the lens rather than clearing a fragment behind it and `←`/`→` do not
   fire twice — once for chip selection and once for the batch. */
const suspended = computed(() => lens.value !== null)
const manifest = ref(false)
const sheets = ref<ApprovedSheet[]>([])
const selectedChip = ref<number | null>(null)

const clock = (at: number | null) =>
  at === null ? null : new Date(at * 1000).toLocaleTimeString('en-GB', { hour12: false })

/* The draft's time to the minute. It is rewritten every few seconds while the
   operator types, and a seconds field that ticks under the eye is noise; the
   approved time keeps its seconds, because it is written once and is the
   receipt someone might quote. */
const minute = (at: number | null) =>
  at === null
    ? null
    : new Date(at * 1000).toLocaleTimeString('en-GB', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
      })

const flow = computed(() => batch.info.value?.flow ?? '')

/* The draft receipt outlives the draft file, within one sitting.

   `approve()` unlinks the draft, so after approving there is nothing on disk for
   `GET /api/inputs/{id}` to report -- but the pairing is the whole of "saving is
   not approving", stated without words: two files, two acts, two timestamps
   seconds apart. So what was saved is remembered here and kept beside the
   approved line. An input approved in an earlier sitting shows the approved
   receipt alone, which is the truth about it. */
const lastDraft = ref<{ name: string; saved: number | null } | null>(null)

// The payload, not the draft's name: every input's draft is `001.draft.json`,
// so watching the name fires on the first load and never again.
watch(sheet.detail, (body) => {
  if (body?.draft) lastDraft.value = { name: body.draft, saved: body.saved }
})

// Autosave moves the time without changing the payload. `null` is not a time:
// after approval the draft is gone and `saved` goes null, but the moment it was
// last written is exactly what the pairing exists to state.
watch(
  () => sheet.saved.value,
  (at) => {
    if (at !== null && lastDraft.value) lastDraft.value = { ...lastDraft.value, saved: at }
  },
)

const receipt = computed(() =>
  lastDraft.value ? `${flow.value}/review/${lastDraft.value.name}` : null,
)

const approvedReceipt = computed(() =>
  sheet.detail.value?.approved
    ? `${flow.value}/review/${sheet.detail.value.approved}`
    : null,
)

/* `③ sheet — approved` once it is, which is also when the fields go read-only.
   The reading is taken from disk rather than from anything held here: approval
   deletes the draft, so "has no draft" IS "is approved". */
const kicker = computed(() =>
  sheet.detail.value && sheet.readonly.value ? 'approved' : 'draft from the tagger',
)

async function approve(): Promise<void> {
  const id = batch.current.value
  if (!id || sheet.readonly.value) return
  // Awaited, not merely started: the debounced write has to be ON DISK before
  // the approve `POST` goes out, or the artifact is built from the previous
  // draft and the last correction is unlinked along with it.
  await sheet.flush()
  if (!(await approval.approve(id))) return
  // Neither depends on the other's answer; both depend only on the POST landing.
  await Promise.all([batch.refresh(), sheet.open(id)])
  focused.value = null
  selectedChip.value = null
  // Approving the last unapproved input opens the manifest, because at that
  // moment there is no sheet left to review.
  if (batch.allApproved.value) await openManifest()
}

/* The rail already knows every input's dimensions, so the source column draws
   its frame at the right aspect ratio while the payload is still in flight --
   which is what keeps the photograph from reflowing the column when it lands. */
const showing = computed(
  () =>
    sheet.detail.value ??
    batch.inputs.value.find((input) => input.id === batch.current.value) ??
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

/* Which pane holds the focus, read from the document rather than remembered:
   the operator can click into any of them, and a remembered answer would send
   the next `Alt+→` from somewhere they are not. */
function paneNow(): Pane {
  const active = document.activeElement
  if (active instanceof HTMLElement) {
    if (active.closest('.rail')) return 'rail'
    if (active.closest('.source')) return 'source'
    if (active.closest('.form')) return 'sheet'
  }
  return pane
}

function enter(next: Pane): void {
  pane = next
  if (next === 'rail') {
    document
      .querySelector<HTMLElement>('.rail__card--current')
      ?.focus()
  } else if (next === 'source') {
    source.value?.focus()
  } else {
    const order = batch.info.value?.schema ?? []
    const field = lastField.value ?? order[0]
    if (field) document.querySelector<HTMLInputElement>(`input.fragment[data-field="${field}"]`)?.focus()
  }
}

function movePane(direction: -1 | 1): void {
  const at = PANES.indexOf(paneNow())
  enter(PANES[Math.min(Math.max(at + direction, 0), PANES.length - 1)])
}

/* The manifest is the closing screen, and it is read from the directory rather
   than remembered: every approved input is asked for its own token count and the
   time its artifact was written. Reached by approving the last unapproved input,
   or from the rail's `run` entry at any point in the batch. */
async function openManifest(): Promise<void> {
  const approved = batch.inputs.value.filter((i) => i.status === 'approved')
  sheets.value = await Promise.all(
    approved.map(async (input) => {
      const body = await inputDetail(input.id)
      return {
        id: input.id,
        name: body.approved ?? '',
        tokens: body.budget.total,
        at: clock(body.approved_at) ?? '',
      } satisfies ApprovedSheet
    }),
  )
  manifest.value = true
}

/* Walk the sheet with the vertical keys, clamped at both ends. A 16-row list
   that jumped from `count` to `background` on one ↑ would lose the operator's
   place rather than move it, which is the same reason the dropdown overlays. */
function moveRow(direction: -1 | 1): void {
  const order = batch.info.value?.schema ?? []
  const at = focused.value ? order.indexOf(focused.value) : -1
  if (at < 0) return
  const next = order[Math.min(Math.max(at + direction, 0), order.length - 1)]
  document
    .querySelector<HTMLInputElement>(`input.fragment[data-field="${next}"]`)
    ?.focus()
}

function commit(field: string, tag: string): void {
  sheet.commit(field, tag, selectedChip.value)
  selectedChip.value = null
  batch.markEdited(batch.current.value)
}

function back(field: string): void {
  const count = chips(field)
  if (count === 0) return
  const at = selectedChip.value ?? count - 1
  sheet.remove(field, at)
  selectedChip.value = null
  batch.markEdited(batch.current.value)
}

/* Open a lens from wherever the focus is. `blur()` rather than a flag: the field
   must stop receiving keys, and the lens's own input takes the focus on mount.
   The fragment survives untouched because `TagInput` stays mounted behind the
   lens — nothing is copied out and copied back, so nothing can come back
   different. Every path that opens a lens goes through here, including the click
   on the photograph. */
async function openLens(which: Lens): Promise<void> {
  if (which === 'cheatsheet' && !candidates.value) {
    candidates.value = await fieldCandidates()
  }
  if (document.activeElement instanceof HTMLElement) document.activeElement.blur()
  lens.value = which
}

/* Give the criterion back exactly. `enter('sheet')` focuses `lastField`, which
   is what the operator was typing into, and `focus()` keeps the two in step. */
function closeLens(): void {
  lens.value = null
  void nextTick(() => enter('sheet'))
}

function toggleLens(which: Lens): void {
  if (lens.value === which) closeLens()
  else void openLens(which)
}

function onKey(event: KeyboardEvent): void {
  const meta = event.metaKey || event.ctrlKey
  /* **Option is a character-producing modifier on macOS**, so both of these match
     `event.code` and both call `preventDefault()`. `Option+Space` emits U+00A0 and
     `Option+F` emits `ƒ`; an `event.key` branch would let the character through
     into a tag field, which is the silent dead end this feature exists to remove.
     `preventDefault()` is load-bearing a second time because Space is the native
     activation key of a focused `<button>`, and this app focuses one on mount. */
  if (event.altKey && event.code === 'Space') {
    event.preventDefault()
    toggleLens('cheatsheet')
    return
  }
  if (event.altKey && event.code === 'KeyF') {
    event.preventDefault()
    if (lens.value === 'photo' || sheet.detail.value) toggleLens('photo')
    return
  }
  /* `event.code`, for the reason stated above: under a Cyrillic layout `Cmd+Z`
     produces `event.key === 'я'` and this branch did nothing at all. The physical
     key is what an undo shortcut names. */
  if (meta && event.code === 'KeyZ') {
    event.preventDefault()
    if (event.shiftKey) sheet.redo()
    else sheet.undo()
  } else if (event.altKey && (event.key === 'ArrowUp' || event.key === 'ArrowDown')) {
    // The rail is a vertical list, so vertical is the batch.
    event.preventDefault()
    batch.step(event.key === 'ArrowUp' ? -1 : 1)
  } else if (event.altKey && (event.key === 'ArrowLeft' || event.key === 'ArrowRight')) {
    event.preventDefault()
    movePane(event.key === 'ArrowLeft' ? -1 : 1)
  } else if (
    !event.altKey &&
    !meta &&
    (event.key === 'ArrowUp' || event.key === 'ArrowDown')
  ) {
    const here = paneNow()
    if (here === 'rail') {
      // A list answers its own arrows.
      event.preventDefault()
      batch.step(event.key === 'ArrowUp' ? -1 : 1)
    } else if (here === 'source') {
      event.preventDefault()
      source.value?.scrollBy({ top: event.key === 'ArrowUp' ? -120 : 120 })
    }
  } else if (meta && event.key === 'Enter') {
    event.preventDefault()
    void approve()
  } else if (event.key === 'Escape' && suspended.value) {
    event.preventDefault()
    closeLens()
  } else if (
    lens.value === 'photo' &&
    (event.key === 'ArrowLeft' || event.key === 'ArrowRight')
  ) {
    // Arrow keys still move through the batch, so the overlay doubles as a way
    // to compare inputs without closing it.
    event.preventDefault()
    batch.step(event.key === 'ArrowLeft' ? -1 : 1)
  }
}

// The draft is written before the tab goes, so a close mid-debounce loses
// nothing. Nothing lives only in the browser.
const onLeave = () => void sheet.flush()

onMounted(async () => {
  window.addEventListener('keydown', onKey)
  window.addEventListener('beforeunload', onLeave)
  await batch.load()
  // The rail first: it is where the operator decides what they are looking at.
  await nextTick()
  enter('rail')
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  window.removeEventListener('beforeunload', onLeave)
})

watch(batch.current, (id) => {
  if (!id) return
  // The pending write belongs to the input being left, not the one arriving.
  // Not awaited: `flush()` captures the id it is writing and `open()` guards on
  // `current`, so the two cannot cross.
  void sheet.flush()
  focused.value = null
  selectedChip.value = null
  approval.forget()
  lastField.value = null
  lastDraft.value = null
  void sheet.open(id).then(() => enter(paneNow()))
})
</script>

<template>
  <div class="shell">
    <AppHeader
      :flow="flow"
      :inputs="batch.inputs.value.length"
      :approved="batch.info.value?.approved ?? 0"
      :draft="receipt"
      :saved="minute(lastDraft?.saved ?? null)"
      :saving="sheet.saving.value"
      :approved-name="approvedReceipt"
      :approved-at="clock(approval.at.value)"
      :refusal="approval.refusal.value ?? sheet.refusal.value ?? batch.failure.value"
    >
      <template #status>
        <LoadingSkeleton
          v-if="batch.loading.value || sheet.loading.value"
          :reading="batch.loading.value ? null : batch.current.value"
          :vocabulary="batch.info.value?.vocabulary ?? 0"
        />
        <span
          v-else-if="batch.allApproved.value"
          class="app-header__receipt--approved mono"
          style="font-size: 11.5px"
        >
          nothing left to review
        </span>
      </template>
    </AppHeader>
    <div v-if="batch.info.value" class="work">
      <BatchRail
        :inputs="batch.inputs.value"
        :current="batch.current.value"
        :edited="batch.edited.value"
        :photo-url="photoUrl"
        :loading="batch.loading.value"
        @select="(id) => ((manifest = false), batch.select(id))"
        @manifest="openManifest"
      />

      <RunManifest
        v-if="manifest"
        :flow="flow"
        :sheets="sheets"
        :total="batch.inputs.value.length"
        @again="manifest = false"
      />

      <template v-else>
      <SourcePanel
        v-if="showing"
        ref="source"
        :id="showing.id"
        :width="showing.width"
        :height="showing.height"
        :photo="photoUrl(showing.id)"
        :caption="sheet.detail.value?.caption ?? null"
        :wd14="sheet.detail.value?.wd14 ?? null"
        :tags="sheet.detail.value?.tags ?? null"
        :loading="sheet.loading.value"
        @open="openLens('photo')"
      />
      <SheetForm
        :schema="batch.info.value?.schema ?? []"
        :fields="sheet.fields.value"
        :budget="sheet.budget.value"
        :readonly="sheet.readonly.value"
        :focused="focused"
        :selected="selectedChip"
        :loading="sheet.loading.value"
        :kicker="kicker"
        @remove="(field, index) => (sheet.remove(field, index), batch.markEdited(batch.current.value))"
      >
        <template #editor="{ field }">
          <TagInput
            v-if="!sheet.readonly.value && !sheet.loading.value"
            :vocabulary="batch.info.value?.vocabulary ?? 0"
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
        <template #footer>
          <ApproveBar
            :approved="sheet.readonly.value"
            :at="clock(approval.at.value)"
            :file="approvedReceipt"
            :working="approval.working.value"
            @approve="approve"
          />
        </template>
      </SheetForm>
      </template>
    </div>

    <PhotoOverlay
      v-if="lens === 'photo' && sheet.detail.value"
      :id="sheet.detail.value.id"
      :width="sheet.detail.value.width"
      :height="sheet.detail.value.height"
      :photo="photoUrl(sheet.detail.value.id)"
      :caption="sheet.detail.value.caption"
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
