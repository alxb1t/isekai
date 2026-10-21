<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import { fieldCandidates, photoUrl as photoAt } from '../api'
import AppHeader from '../components/AppHeader.vue'
import ApproveBar from '../components/ApproveBar.vue'
import BatchRail from '../components/BatchRail.vue'
import CheatsheetOverlay from '../components/CheatsheetOverlay.vue'
import LoadingSkeleton from '../components/LoadingSkeleton.vue'
import PhotoOverlay from '../components/PhotoOverlay.vue'
import RefusalPage from '../components/RefusalPage.vue'
import RendersBlock from '../components/RendersBlock.vue'
import SheetForm from '../components/SheetForm.vue'
import SourcePanel from '../components/SourcePanel.vue'
import TagInput from '../components/TagInput.vue'
import { useApproval } from '../composables/useApproval'
import { after, queue, useQueue } from '../composables/useQueue'
import { useSheet } from '../composables/useSheet'
import type { FieldCandidates } from '../types'

/* Review: one batch in one flow, the run in the URL. It shows the loading state
   or the review layout; the photo overlay layers over either. The router keys
   this view by batch and flow, so a new digest is a new sheet in the same view.

   It owns the global keyboard model -- the bindings that cross components, so
   no component ends up owning two of them -- and the chip selection for the
   focused field, because the chips render in `FieldRow` while the keys that
   move between them are read by `TagInput`. */
const props = defineProps<{ batch: string; digest: string; flow: string }>()
const router = useRouter()
const batch = useQueue(props.batch, props.flow, () => props.digest)
const failure = ref<string | null>(null)
const done = computed(() => batch.info.value !== null && queue(batch.info.value, props.flow).length === 0)
/* A refusal after the approval landed: the approval stands, and the bar says
   what could not be read next. */
const afterApproval = ref<string | null>(null)
const sheet = useSheet({ batch: props.batch, flow: props.flow })
const approval = useApproval()
const current = computed(() => props.digest)
const photoUrl = (digest: string) => photoAt({ batch: props.batch, digest, flow: props.flow })
const schema = computed(() => sheet.detail.value?.schema ?? [])
const vocabulary = computed(() => sheet.detail.value?.vocabulary ?? 0)

/* The URL is the state: choosing another sheet is a navigation. */
function select(digest: string): void {
  if (digest !== props.digest)
    void router.push({ name: 'review', params: { ...props, digest } })
}

function stepBatch(direction: -1 | 1): void {
  const inputs = batch.inputs.value
  const at = inputs.findIndex((i) => i.id === props.digest)
  if (at < 0 || inputs.length === 0) return
  select(inputs[(at + direction + inputs.length) % inputs.length].id)
}

/* Three panes, left to right: the rail, the photograph and its caption, the
   sheet. `Alt+←/→` moves between them and `Alt+↑/↓` moves through the batch;
   inside a pane the plain arrows do that pane's own thing — scroll the caption,
   walk the rows, change the input.

   The rail is a vertical list, so vertical is the batch, and horizontal is
   getting to the caption to read it, and back to the field being typed. */
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

const flow = computed(() => props.flow)

/* The draft receipt outlives the draft file, within one sitting.

   `approve()` unlinks the draft, so after approving there is nothing on disk for
   the review payload to report -- but the pairing is the whole of "saving is
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
   The reading is taken from disk rather than from anything held here. It is NOT
   "has no draft": `review --new-version` writes a draft beside the approved
   artifact, and that input is re-opened -- editable, and carrying a correction
   the tagger did not write. */
const kicker = computed(() => {
  // No approved artifact is the tagger's draft, whether or not the payload has
  // arrived -- `readonly` defaults to true while `detail` is null, so testing
  // it first would call an unloaded sheet approved.
  if (!sheet.detail.value?.approved) return 'draft from the tagger'
  return sheet.readonly.value ? 'approved' : 're-opened'
})

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
  // on the header line; stopping here is what makes it true.
  if (!(await sheet.flush())) return
  const place = { batch: props.batch, digest: id, flow: props.flow }
  if (!(await approval.approve(place, sheet.saved.value))) return
  // Neither depends on the other's answer; both depend only on the POST landing.
  // The sheet is re-read so the page shows it approved, whatever follows.
  const [read] = await Promise.allSettled([batch.load(), sheet.open(id)])
  focused.value = null
  selectedChip.value = null
  if (read.status === 'rejected') {
    afterApproval.value = (read.reason as Error).message
    return
  }
  const next = after(read.value, props.flow, id)
  if (next) select(next)
  else void router.push({ name: 'hub', params: { batch: props.batch } })
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
    const order = schema.value
    const field = lastField.value ?? order[0]
    if (field) document.querySelector<HTMLInputElement>(`input.fragment[data-field="${field}"]`)?.focus()
  }
}

function movePane(direction: -1 | 1): void {
  const at = PANES.indexOf(paneNow())
  enter(PANES[Math.min(Math.max(at + direction, 0), PANES.length - 1)])
}

/* Walk the sheet with the vertical keys, clamped at both ends. A 16-row list
   that jumped from `count` to `background` on one ↑ would lose the operator's
   place rather than move it, which is the same reason the dropdown overlays. */
function moveRow(direction: -1 | 1): void {
  const order = schema.value
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
  if (which === 'cheatsheet' && !candidates.value) {
    candidates.value = await fieldCandidates(props.flow)
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
  /* **Both properties, because `Cmd+Z` produces no character.** Either test
     alone is partial: under a Cyrillic layout `event.key` is `'я'`, and under
     Dvorak `code: 'KeyZ'` is the key printed `;` while the key printed `Z`
     reports `code: 'Slash'`. This is not the Option case above -- Option emits a
     character, so `event.key` there is unusable and only the physical key will
     do; a meta-modified Z emits nothing, so accepting both swallows no text. */
  if (meta && (event.key.toLowerCase() === 'z' || event.code === 'KeyZ')) {
    event.preventDefault()
    if (event.shiftKey) sheet.redo()
    else sheet.undo()
  } else if (event.altKey && (event.key === 'ArrowUp' || event.key === 'ArrowDown')) {
    // The rail is a vertical list, so vertical is the batch.
    event.preventDefault()
    stepBatch(event.key === 'ArrowUp' ? -1 : 1)
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
      stepBatch(event.key === 'ArrowUp' ? -1 : 1)
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
    stepBatch(event.key === 'ArrowLeft' ? -1 : 1)
  }
}

// The draft is flushed as the tab goes; the PUT is kept alive past the page.
const onLeave = () => void sheet.flush()

// Leaving for another screen flushes too; the draft is the operator's work.
onBeforeRouteLeave(async () => {
  await sheet.flush()
})

onMounted(async () => {
  window.addEventListener('keydown', onKey)
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

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  window.removeEventListener('beforeunload', onLeave)
})

watch(current, (id) => {
  if (!id) return
  // The pending write belongs to the input being left, not the one arriving.
  // Not awaited: `flush()` captures the id it is writing and `open()` guards on
  // `current`, so the two cannot cross.
  void sheet.flush()
  focused.value = null
  selectedChip.value = null
  approval.forget()
  afterApproval.value = null
  lastField.value = null
  lastDraft.value = null
  void sheet.open(id).then(() => enter(paneNow()))
})
</script>

<template>
  <RefusalPage v-if="failure" :refusal="failure" />
  <div v-else class="review">
    <AppHeader
      :flow="flow"
      :inputs="batch.sheets.value"
      :approved="batch.approved.value"
      :draft="receipt"
      :saved="minute(lastDraft?.saved ?? null)"
      :saving="sheet.saving.value"
      :approved-name="approvedReceipt"
      :approved-at="clock(approval.at.value)"
      :refusal="approval.refusal.value ?? sheet.refusal.value"
    >
      <template #status>
        <LoadingSkeleton
          v-if="batch.loading.value || sheet.loading.value"
          :reading="batch.loading.value ? null : current"
          :vocabulary="vocabulary"
        />
        <span
          v-else-if="done"
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
        :approved="batch.approved.value"
        :sheets="batch.sheets.value"
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
        @open="openLens('photo')"
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
        <template #footer>
          <RendersBlock
            v-if="!sheet.loading.value"
            :renders="sheet.renders.value"
            :readonly="sheet.readonly.value"
            @change="sheet.setRenders"
          />
          <ApproveBar
            :approved="sheet.readonly.value"
            :at="clock(approval.at.value)"
            :file="approvedReceipt"
            :working="approval.working.value"
            :refusal="afterApproval"
            @approve="approve"
          />
        </template>
      </SheetForm>
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
