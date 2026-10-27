<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useHeldFocus } from '../composables/useHeldFocus'
import { type PickTile, type SourceGrid, imageName, movePick, pickHead, tileCaption } from '../cells'
import { useKeys } from '../composables/useKeys'
import type { Focus, Move } from '../grid'
import { plain } from '../stores/keys'

/* *Compare with…* (design spec J5·2): the source's images as a grid in a modal
   dialog that holds the focus — the photograph's row on top, then a row per
   flow, oldest first, each tile captioned by its version, the image compare
   started from marked, the head naming the focused tile's flow, version and seed.
   `h j k l` and the arrows move, `↵` or a click compares, `Esc` goes back. */
const props = defineProps<{
  from: NonNullable<PickTile>
  grid: SourceGrid
  src: (tile: PickTile) => string
}>()

const emit = defineEmits<{ pick: [tile: PickTile]; close: [] }>()

const dialog = ref<HTMLDialogElement | null>(null)
const focus = ref<Focus>(props.grid.start)
const head = computed(() =>
  pickHead(props.from, props.grid.rows[focus.value.row]?.tiles[focus.value.column] ?? null),
)

const isOrigin = (row: number, column: number) =>
  row === props.grid.origin.row && column === props.grid.origin.column

async function show(at: Focus): Promise<void> {
  focus.value = at
  await nextTick()
  dialog.value
    ?.querySelector<HTMLElement>(`[data-row="${at.row}"][data-column="${at.column}"]`)
    ?.focus()
}

const walk = (move: Move) => void show(movePick(props.grid, focus.value, move))

/* The image compare started from is marked, never compared with itself. */
function choose(row: number, column: number): void {
  if (!isOrigin(row, column)) emit('pick', props.grid.rows[row].tiles[column])
}

useKeys('overlay', [
  { id: 'close', keys: plain('Escape'), label: 'back', run: () => dialog.value?.close() },
  { id: 'left', keys: plain('KeyH', 'ArrowLeft'), label: 'previous', run: () => walk('column-') },
  { id: 'right', keys: plain('KeyL', 'ArrowRight'), label: 'next', run: () => walk('column+') },
  { id: 'down', keys: plain('KeyJ', 'ArrowDown'), label: 'row down', run: () => walk('row+') },
  { id: 'up', keys: plain('KeyK', 'ArrowUp'), label: 'row up', run: () => walk('row-') },
  {
    id: 'compare',
    keys: plain('Enter'),
    label: 'compare',
    run: () => choose(focus.value.row, focus.value.column),
    when: () => !isOrigin(focus.value.row, focus.value.column),
  },
])

useHeldFocus(dialog, () => dialog.value?.close())
onMounted(() => {
  dialog.value?.showModal()
  void show(props.grid.start)
})
</script>

<template>
  <dialog
    ref="dialog"
    class="viewer"
    :aria-label="head"
    data-compare-pick
    @close="emit('close')"
  >
    <p class="viewer__title mono" data-pick-head>{{ head }}</p>
    <div class="pick">
      <div v-for="(line, row) in grid.rows" :key="line.flow ?? 'photo'" class="pick__row">
        <span class="pick__flow mono">{{ line.flow ?? 'photo' }}</span>
        <div class="pick__tiles">
          <figure
            v-for="(tile, column) in line.tiles"
            :key="tile ? `${tile.version}/${tile.seed}` : 'photo'"
            class="pick__tile"
          >
            <button
              class="renders__image"
              :class="{ 'renders__image--selected': isOrigin(row, column) }"
              type="button"
              :data-row="row"
              :data-column="column"
              :data-origin="isOrigin(row, column) || undefined"
              :aria-label="imageName(tile)"
              @focus="focus = { row, column }"
              @click="choose(row, column)"
            >
              <img :src="src(tile)" alt="" />
            </button>
            <figcaption class="mono">{{ tileCaption(tile) }}</figcaption>
          </figure>
        </div>
      </div>
    </div>
  </dialog>
</template>
