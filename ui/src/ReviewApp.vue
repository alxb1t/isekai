<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { photoUrl } from './api'
import AppHeader from './components/AppHeader.vue'
import ApproveBar from './components/ApproveBar.vue'
import BatchRail from './components/BatchRail.vue'
import SheetForm from './components/SheetForm.vue'
import SourcePanel from './components/SourcePanel.vue'
import TagInput from './components/TagInput.vue'
import { useApproval } from './composables/useApproval'
import { useBatch } from './composables/useBatch'
import { useSheet } from './composables/useSheet'

/* The root. It shows exactly one of the loading state, the review layout, or
   the manifest; the photo overlay layers over any of them.

   It owns the global keyboard model -- the bindings that cross components, so
   no component ends up owning two of them -- and the chip selection for the
   focused field, because the chips render in `FieldRow` while the keys that
   move between them are read by `TagInput`. */
const batch = useBatch()
const sheet = useSheet()
const approval = useApproval()

const focused = ref<string | null>(null)
const selectedChip = ref<number | null>(null)

const clock = (at: number | null) =>
  at === null ? null : new Date(at * 1000).toLocaleTimeString('en-GB', { hour12: false })

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
  sheet.readonly.value ? 'approved' : 'draft from the sorter',
)

async function approve(): Promise<void> {
  const id = batch.current.value
  if (!id || sheet.readonly.value) return
  // The debounced write lands before the approve, so the artifact is taken from
  // what the operator last typed rather than from what happened to be on disk.
  sheet.flush()
  if (!(await approval.approve(id))) return
  await batch.refresh()
  await sheet.open(id)
  focused.value = null
  selectedChip.value = null
}

const chips = (field: string | null) => (field ? (sheet.fields.value[field] ?? []).length : 0)

function focus(field: string): void {
  focused.value = field
  selectedChip.value = null
}

function step(direction: -1 | 1): void {
  const count = chips(focused.value)
  if (count === 0) return
  const at = selectedChip.value
  if (at === null) selectedChip.value = direction === -1 ? count - 1 : 0
  else selectedChip.value = (at + direction + count) % count
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

function onKey(event: KeyboardEvent): void {
  const meta = event.metaKey || event.ctrlKey
  if (meta && event.key.toLowerCase() === 'z') {
    event.preventDefault()
    if (event.shiftKey) sheet.redo()
    else sheet.undo()
  } else if (event.altKey && (event.key === 'ArrowLeft' || event.key === 'ArrowRight')) {
    event.preventDefault()
    batch.step(event.key === 'ArrowLeft' ? -1 : 1)
  } else if (meta && event.key === 'Enter') {
    event.preventDefault()
    void approve()
  }
}

// The draft is written before the tab goes, so a close mid-debounce loses
// nothing. Nothing lives only in the browser.
const onLeave = () => sheet.flush()

onMounted(async () => {
  window.addEventListener('keydown', onKey)
  window.addEventListener('beforeunload', onLeave)
  await batch.load()
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  window.removeEventListener('beforeunload', onLeave)
})

watch(batch.current, (id) => {
  if (!id) return
  // The pending write belongs to the input being left, not the one arriving.
  sheet.flush()
  focused.value = null
  selectedChip.value = null
  approval.forget()
  lastDraft.value = null
  void sheet.open(id)
})
</script>

<template>
  <div class="shell">
    <AppHeader
      :flow="flow"
      :inputs="batch.inputs.value.length"
      :approved="batch.info.value?.approved ?? 0"
      :draft="receipt"
      :saved="clock(lastDraft?.saved ?? null)"
      :approved-name="approvedReceipt"
      :approved-at="clock(approval.at.value)"
      :refusal="approval.refusal.value ?? sheet.refusal.value ?? batch.failure.value"
    />
    <div class="work">
      <BatchRail
        :inputs="batch.inputs.value"
        :current="batch.current.value"
        :edited="batch.edited.value"
        :photo-url="photoUrl"
        :loading="batch.loading.value"
        @select="batch.select"
      />
      <SourcePanel
        v-if="sheet.detail.value"
        :id="sheet.detail.value.id"
        :width="sheet.detail.value.width"
        :height="sheet.detail.value.height"
        :photo="photoUrl(sheet.detail.value.id)"
        :caption="sheet.detail.value.caption"
        :loading="sheet.loading.value"
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
    </div>
  </div>
</template>
