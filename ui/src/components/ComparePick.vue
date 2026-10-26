<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useKeys } from '../composables/useKeys'
import { plain } from '../stores/keys'

/* *Compare with…* (design spec J5·2): the cell's other images as tiles, oldest
   first, each named by its version and seed, in a modal dialog that holds the
   focus. `h j k l` and the arrows move, `↵` or a click compares, `Esc` goes back. */
const props = defineProps<{
  title: string
  images: { src: string; version: number; seed: string }[]
  start: number
}>()

const emit = defineEmits<{ pick: [index: number]; close: [] }>()

const dialog = ref<HTMLDialogElement | null>(null)

function tiles(): HTMLElement[] {
  return [...(dialog.value?.querySelectorAll<HTMLElement>('[data-pick]') ?? [])]
}
const at = () => tiles().indexOf(document.activeElement as HTMLElement)

/* A row's length, read from the layout: the first tile set lower starts the next. */
function perRow(held: HTMLElement[]): number {
  const next = held.findIndex((one) => one.offsetTop !== held[0].offsetTop)
  return next < 0 ? held.length : next
}

function walk(rows: number, columns: number): void {
  const held = tiles()
  if (!held.length) return
  const next = at() + rows * perRow(held) + columns
  held[Math.min(Math.max(next, 0), held.length - 1)].focus()
}

/* The dialog itself is the backdrop's target: a click on a tile lands on it. */
function outside(event: MouseEvent): void {
  if (event.target === dialog.value) dialog.value?.close()
}

useKeys('overlay', [
  { id: 'close', keys: plain('Escape'), label: 'back', run: () => dialog.value?.close() },
  { id: 'left', keys: plain('KeyH', 'ArrowLeft'), label: 'previous', run: () => walk(0, -1) },
  { id: 'right', keys: plain('KeyL', 'ArrowRight'), label: 'next', run: () => walk(0, 1) },
  { id: 'down', keys: plain('KeyJ', 'ArrowDown'), label: 'row down', run: () => walk(1, 0) },
  { id: 'up', keys: plain('KeyK', 'ArrowUp'), label: 'row up', run: () => walk(-1, 0) },
  {
    id: 'compare',
    keys: plain('Enter'),
    label: 'compare',
    run: () => emit('pick', at()),
    when: () => at() >= 0,
  },
])

onMounted(() => {
  dialog.value?.showModal()
  tiles()[props.start]?.focus()
})
</script>

<template>
  <dialog
    ref="dialog"
    class="viewer"
    :aria-label="title"
    data-compare-pick
    @click="outside"
    @close="emit('close')"
  >
    <p class="viewer__title mono">{{ title }}</p>
    <div class="pick">
      <figure v-for="(one, index) in images" :key="`${one.version}/${one.seed}`" class="pick__tile">
        <button
          class="renders__image"
          type="button"
          data-pick
          :aria-label="`v${one.version} · seed ${one.seed}`"
          @click="emit('pick', index)"
        >
          <img :src="one.src" alt="" />
        </button>
        <figcaption class="mono">v{{ one.version }} · seed {{ one.seed }}</figcaption>
      </figure>
    </div>
  </dialog>
</template>
