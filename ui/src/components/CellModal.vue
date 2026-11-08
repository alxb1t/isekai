<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useHeldFocus } from '../composables/useHeldFocus'
import { type CellGrid, type PickTile, imageName, movePick } from '../cells'
import { useKeys } from '../composables/useKeys'
import type { Focus, Move } from '../grid'
import { plain } from '../stores/keys'

/* The cell modal (design spec J2): a hub cell's renders as a grid in a modal
   dialog that holds the focus — a row per version, oldest first, each its seeds
   in numeric order, at twice a thumbnail's size, a seed rendered under more than
   one version marked ⇄, the head naming the source and the focused image.
   `h j k l` and the arrows move, `↵` or a click opens its large view, `Esc` closes. */
const props = defineProps<{
  title: string
  grid: CellGrid
  src: (tile: NonNullable<PickTile>) => string
}>()

const emit = defineEmits<{ open: [tile: NonNullable<PickTile>]; close: [] }>()

const dialog = ref<HTMLDialogElement | null>(null)
const focus = ref<Focus>(props.grid.start)
const focused = computed(() => props.grid.rows[focus.value.row]?.tiles[focus.value.column])
const head = computed(() =>
  focused.value ? `${props.title} · ${imageName(focused.value)}` : props.title,
)

async function show(at: Focus): Promise<void> {
  focus.value = at
  await nextTick()
  dialog.value
    ?.querySelector<HTMLElement>(`[data-row="${at.row}"][data-column="${at.column}"]`)
    ?.focus()
}

const walk = (move: Move) => void show(movePick(props.grid, focus.value, move))

function choose(): void {
  if (focused.value) emit('open', focused.value)
}

useKeys('overlay', [
  { id: 'close', keys: plain('Escape'), label: 'close', run: () => dialog.value?.close() },
  { id: 'left', keys: plain('KeyH', 'ArrowLeft'), label: 'previous', run: () => walk('column-') },
  { id: 'right', keys: plain('KeyL', 'ArrowRight'), label: 'next', run: () => walk('column+') },
  { id: 'down', keys: plain('KeyJ', 'ArrowDown'), label: 'row down', run: () => walk('row+') },
  { id: 'up', keys: plain('KeyK', 'ArrowUp'), label: 'row up', run: () => walk('row-') },
  { id: 'open', keys: plain('Enter'), label: 'large view', run: choose },
])

useHeldFocus(dialog, () => dialog.value?.close())
onMounted(() => {
  dialog.value?.showModal()
  void show(props.grid.start)
})
</script>

<template>
  <dialog ref="dialog" class="viewer" :aria-label="head" data-cell-modal @close="emit('close')">
    <p class="viewer__title mono">{{ head }}</p>
    <div class="pick pick--cell">
      <div v-for="(line, row) in grid.rows" :key="line.version" class="pick__row">
        <span class="pick__flow mono">v{{ line.version }}</span>
        <div class="pick__tiles">
          <figure v-for="(tile, column) in line.tiles" :key="tile.seed" class="pick__tile">
            <button
              class="renders__image"
              type="button"
              :data-row="row"
              :data-column="column"
              :data-version="tile.version"
              :data-seed="tile.seed"
              :aria-label="imageName(tile)"
              @focus="focus = { row, column }"
              @click="emit('open', tile)"
            >
              <img :src="src(tile)" alt="" />
            </button>
            <figcaption class="mono">
              seed {{ tile.seed }}<span v-if="grid.shared.has(tile.seed)" data-shared> ⇄</span>
            </figcaption>
          </figure>
        </div>
      </div>
    </div>
  </dialog>
</template>
