<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { photoUrl } from './api'
import AppHeader from './components/AppHeader.vue'
import BatchRail from './components/BatchRail.vue'
import SheetForm from './components/SheetForm.vue'
import SourcePanel from './components/SourcePanel.vue'
import TagInput from './components/TagInput.vue'
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

const focused = ref<string | null>(null)
const selectedChip = ref<number | null>(null)

const clock = (at: number | null) =>
  at === null ? null : new Date(at * 1000).toLocaleTimeString('en-GB', { hour12: false })

const flow = computed(() => batch.info.value?.flow ?? '')

const receipt = computed(() =>
  sheet.detail.value?.draft ? `${flow.value}/review/${sheet.detail.value.draft}` : null,
)

const approvedReceipt = computed(() =>
  sheet.detail.value?.approved
    ? `${flow.value}/review/${sheet.detail.value.approved}`
    : null,
)

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
      :saved="clock(sheet.saved.value)"
      :approved-name="approvedReceipt"
      :approved-at="null"
      :refusal="sheet.refusal.value ?? batch.failure.value"
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
        kicker="draft from the sorter"
        @remove="(field, index) => (sheet.remove(field, index), batch.markEdited(batch.current.value))"
      >
        <template #editor="{ field }">
          <TagInput
            v-if="!sheet.readonly.value && !sheet.loading.value"
            :vocabulary="batch.info.value?.vocabulary ?? 0"
            :focused="focused === field"
            :chips="chips(field)"
            :selected="focused === field ? selectedChip : null"
            @focus="focus(field)"
            @blur="focused === field && (focused = null)"
            @commit="(tag) => commit(field, tag)"
            @back="back(field)"
            @step="step"
          />
        </template>
      </SheetForm>
    </div>
  </div>
</template>
