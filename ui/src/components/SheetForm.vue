<script setup lang="ts">
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
  /* The draft's save: in flight, or the time it landed. */
  saving?: boolean
  saved?: string | null
  focused: string | null
  selected: number | null
  loading?: boolean
  /* The approval a revision was copied from, whose fields each row is read against. */
  previous?: Record<string, string[]> | null
}>()

defineEmits<{ remove: [field: string, index: number] }>()

function was(name: string): string[] | null {
  if (!props.previous) return null
  const held = props.previous[name] ?? []
  const now = props.fields[name] ?? []
  const same = held.length === now.length && held.every((tag, index) => tag === now[index])
  return same ? null : held
}

function state(name: string): 'filled' | 'empty' | 'pending' {
  if (props.loading) return 'pending'
  return (props.fields[name] ?? []).length > 0 ? 'filled' : 'empty'
}
</script>

<template>
  <section class="form">
    <SheetHeader :kicker="kicker" :budget="budget" :saving="saving" :saved="saved" />
    <div class="form__body">
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
        :was="was(name)"
        @remove="(index) => $emit('remove', name, index)"
      >
          <slot name="editor" :field="name" />
        </FieldRow>
      </div>
      <!-- ④, right of the rows. -->
      <slot name="aside" />
    </div>
    <slot name="footer" />
  </section>
</template>
