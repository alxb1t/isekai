<script setup lang="ts">
import StatusMark from './StatusMark.vue'
import TagChip from './TagChip.vue'

/* One schema field. The key is rendered verbatim in monospace, because the
   operator wrote the schema and the keys are the clearer language.

   Frame delta 5: an empty field reads the italic word `empty` with a hollow
   gutter ring, and nothing offers to mark it intentional. The ring still says
   *not filled*; nothing insists that it should be. */
defineProps<{
  fieldKey: string
  tags: string[]
  tokens: number
  state: 'filled' | 'empty' | 'pending'
  readonly: boolean
  focused: boolean
  selected?: number | null
}>()

defineEmits<{ remove: [index: number] }>()

/* Click anywhere in the row to type in it.

   The fragment input is sized to its content, because the 1px accent caret has
   to sit immediately after the text rather than at the row's right edge -- so on
   an empty field the input itself is one character wide and all but unhittable.
   The row is the target the operator actually aims at, and a row is 34px of
   mostly empty space, so the whole of it focuses the field. */
function focusFragment(event: MouseEvent): void {
  const row = event.currentTarget as HTMLElement
  row.querySelector<HTMLInputElement>('input.fragment')?.focus()
}
</script>

<template>
  <div class="row" :class="{ 'row--focused': focused }" @click="focusFragment">
    <StatusMark
      :kind="state === 'pending' ? 'dashed' : state === 'filled' ? 'filled' : 'hollow'"
    />
    <span class="row__key mono">{{ fieldKey }}</span>
    <div class="row__tags">
      <template v-if="state === 'filled'">
        <TagChip
          v-for="(tag, index) in tags"
          :key="`${tag}-${index}`"
          :tag="tag"
          :readonly="readonly"
          :selected="selected === index"
          @remove="$emit('remove', index)"
        />
      </template>
      <span v-else-if="state === 'empty' && !focused" class="row__empty">empty</span>
      <slot />
    </div>
    <span class="row__tokens mono">{{ tokens > 0 ? tokens : '' }}</span>
  </div>
</template>
