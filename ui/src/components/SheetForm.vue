<script setup lang="ts">
import { computed } from 'vue'
import type { Budget } from '../types'
import FieldRow from './FieldRow.vue'
import SheetHeader from './SheetHeader.vue'

/* Every field the schema declares, always open, in schema order, never
   re-sorted. The wall of rows was a density problem rather than a hiding
   problem, so nothing here groups or collapses. */
const props = defineProps<{
  schema: string[]
  fields: Record<string, string[]>
  budget: Budget | null
  readonly: boolean
  kicker: string
  focused: string | null
  selected: number | null
  loading?: boolean
}>()

defineEmits<{ remove: [field: string, index: number] }>()

const filled = computed(
  () => props.schema.filter((name) => (props.fields[name] ?? []).length > 0).length,
)

function state(name: string): 'filled' | 'empty' | 'pending' {
  if (props.loading) return 'pending'
  return (props.fields[name] ?? []).length > 0 ? 'filled' : 'empty'
}
</script>

<template>
  <section class="form">
    <SheetHeader
      :kicker="kicker"
      :fields="schema.length"
      :filled="filled"
      :budget="budget"
    />
    <div class="rows">
      <FieldRow
        v-for="name in schema"
        :key="name"
        :field-key="name"
        :tags="fields[name] ?? []"
        :tokens="budget?.per_field[name] ?? 0"
        :state="state(name)"
        :readonly="readonly"
        :focused="name === focused"
        :selected="name === focused ? selected : null"
        @remove="(index) => $emit('remove', name, index)"
      >
        <slot name="editor" :field="name" />
      </FieldRow>
    </div>
    <slot name="footer" />
  </section>
</template>
