<script setup lang="ts">
import { computed, ref } from 'vue'
import { photoUrl } from './api'
import AppHeader from './components/AppHeader.vue'
import BatchRail from './components/BatchRail.vue'
import SheetForm from './components/SheetForm.vue'
import SourcePanel from './components/SourcePanel.vue'
import TagInput from './components/TagInput.vue'
import { BATCH, DETAIL } from './fixture'

/* The root. It shows exactly one of the loading state, the review layout, or
   the manifest; the photo overlay layers over any of them.

   Reading from the fixture for now -- the shell and the read-only sheet are
   built before any data loading, so that the marks and the rows are right
   before a fetch can be blamed for them. */
const batch = ref(BATCH)
const detail = ref(DETAIL)
const current = ref(BATCH.inputs[0].id)
const edited = ref(new Set<string>())
const refusal = ref<string | null>(null)
const focused = ref<string | null>(null)

const clock = (at: number | null) =>
  at === null ? null : new Date(at * 1000).toLocaleTimeString('en-GB', { hour12: false })

const receipt = computed(() =>
  detail.value.draft ? `${batch.value.flow}/review/${detail.value.draft}` : null,
)

const approvedReceipt = computed(() =>
  detail.value.approved ? `${batch.value.flow}/review/${detail.value.approved}` : null,
)
</script>

<template>
  <div class="shell">
    <AppHeader
      :flow="batch.flow"
      :inputs="batch.inputs.length"
      :approved="batch.approved"
      :draft="receipt"
      :saved="clock(detail.saved)"
      :approved-name="approvedReceipt"
      :approved-at="null"
      :refusal="refusal"
    />
    <div class="work">
      <BatchRail
        :inputs="batch.inputs"
        :current="current"
        :edited="edited"
        :photo-url="photoUrl"
        @select="current = $event"
      />
      <SourcePanel
        :id="detail.id"
        :width="detail.width"
        :height="detail.height"
        :photo="photoUrl(detail.id)"
        :caption="detail.caption"
      />
      <SheetForm
        :schema="batch.schema"
        :fields="detail.fields"
        :budget="detail.budget"
        :readonly="detail.readonly"
        :focused="focused"
        kicker="draft from the sorter"
      >
        <template #editor="{ field }">
          <TagInput
            v-if="!detail.readonly"
            :vocabulary="batch.vocabulary"
            :focused="focused === field"
            @focus="focused = field"
            @blur="focused === field && (focused = null)"
          />
        </template>
      </SheetForm>
    </div>
  </div>
</template>
