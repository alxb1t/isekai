<script setup lang="ts">
import { computed } from 'vue'
import { type Pairs, chosen, lone } from '../pairs'

/* The pairs of a stage as rows, the selected one marked and a proposed pair's row saying
   *proposed*, with undo, delete and clear as buttons. It declares no command. */
const props = defineProps<{ pairs: Pairs; names: [string, string] }>()
const emit = defineEmits<{
  change: [next: Pairs]
  undo: []
  remove: []
  clear: []
}>()

const alone = computed(() => lone(props.pairs))
const rows = computed(() =>
  props.pairs.slots.map((slot, index) => ({
    number: index + 1,
    text:
      slot.a && slot.b
        ? slot.proposed
          ? 'proposed'
          : 'placed'
        : `no match on the ${alone.value?.waiting === 'a' ? props.names[0] : props.names[1]}`,
    proposed: slot.proposed === true,
    on: index === props.pairs.selected,
  })),
)
</script>

<template>
  <aside class="pairlist" data-pairs>
    <span class="section-label">pairs · {{ rows.length }}</span>
    <ol class="pairlist__rows">
      <li v-for="row in rows" :key="row.number">
        <button
          class="pairlist__row mono"
          :class="{ 'pairlist__row--on': row.on }"
          :data-proposed="row.proposed || undefined"
          type="button"
          @click="emit('change', chosen(pairs, row.on ? null : row.number - 1))"
        >
          {{ row.number }} · {{ row.text }}
        </button>
      </li>
    </ol>
    <div class="pairlist__row-bar">
      <button class="btn btn-secondary" type="button" :disabled="pairs.past.length === 0" @click="emit('undo')">
        Undo
      </button>
      <button class="btn btn-secondary" type="button" :disabled="pairs.selected === null" @click="emit('remove')">
        Delete
      </button>
      <button class="btn btn-secondary" type="button" :disabled="pairs.slots.length === 0" @click="emit('clear')">
        Clear
      </button>
    </div>
  </aside>
</template>
