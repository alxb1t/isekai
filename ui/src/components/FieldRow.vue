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
</script>

<template>
  <div class="row" :class="{ 'row--focused': focused }">
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
      <span v-else-if="state === 'empty'" class="row__empty">empty</span>
      <slot />
    </div>
    <span class="row__tokens mono">{{ tokens > 0 ? tokens : '' }}</span>
  </div>
</template>
