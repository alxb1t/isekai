<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useKeys } from '../composables/useKeys'
import { usePair } from '../composables/usePair'
import { useViewer, viewerKeys } from '../composables/useViewer'
import type { Command } from '../stores/keys'

/* Images in a native dialog, fitted to the window. A click on the image or `↵`
   toggles 1:1 pixels, scrolled inside the dialog by `j` `k` `↓` `↑`; `←` `→` `h` `l`
   step through the images, and Esc or a click outside closes. With `pair`, every image stands side by side at one
   height, fit only.
   `commands` are the opener's own keys while it is open, as Review's `⌃P`.
   The list may grow while open, as a live session's does.
   The dialog keeps the URL of the page beneath (design spec §1 rule 8). */
export interface Shown {
  src: string
  name: string
  width?: number | null
  height?: number | null
}

const props = defineProps<{
  images: Shown[]
  start?: number
  pair?: boolean
  commands?: Command[]
}>()

const emit = defineEmits<{ close: [] }>()

const dialog = ref<HTMLDialogElement | null>(null)
const image = ref<HTMLImageElement | null>(null)
const frame = ref<HTMLElement | null>(null)
const viewer = useViewer(() => props.images, props.start ?? 0, () => emit('close'))
const { at, shown, actual, toggle } = viewer
/* The fitted image's scale, measured once it has loaded, on every resize while
   fitted, and on the switch back to fit: at 1:1 the drawn width is the natural one. */
const scale = ref<number | null>(null)

function measure(): void {
  const held = image.value
  if (held && held.naturalWidth > 0 && !actual.value)
    scale.value = Math.round((held.clientWidth / held.naturalWidth) * 100)
}

watch(actual, (now) => {
  if (!now) void nextTick(measure)
})

watch(
  () => shown.value?.src,
  () => {
    scale.value = null
  },
)

const title = computed(() => {
  if (props.pair) return props.images.map((one) => one.name).join(' · ')
  if (!shown.value) return ''
  const { name, width, height } = shown.value
  const size = width && height ? ` · ${width}×${height}` : ''
  const fit = actual.value ? '1:1' : scale.value === null ? 'fit' : `fit ${scale.value}%`
  const place = props.images.length > 1 ? ` · ${at.value + 1} of ${props.images.length}` : ''
  return `${name}${size} · ${fit}${place}`
})

/* The pair, as wide as the window allows and no taller than it. */
const {
  ratios,
  loaded,
  width: pairWidth,
} = usePair(
  props.images.map((one) => (one.width && one.height ? one.width / one.height : 1)),
  'calc(100vw - 64px)',
  '(100vh - 120px)',
)

/* The dialog itself is the backdrop's target: a click on an image or the title
   lands on them instead. */
function outside(event: MouseEvent): void {
  if (event.target === dialog.value) dialog.value?.close()
}

useKeys('overlay', [
  ...viewerKeys(viewer, {
    close: () => dialog.value?.close(),
    scroll: (by) => frame.value?.scrollBy({ top: by }),
    pair: () => props.pair === true,
  }),
  ...(props.commands ?? []),
])

onMounted(() => {
  dialog.value?.showModal()
  window.addEventListener('resize', measure)
})

onUnmounted(() => window.removeEventListener('resize', measure))
</script>

<template>
  <dialog
    ref="dialog"
    class="viewer"
    :class="{ 'viewer--actual': actual }"
    data-viewer
    :data-pair="pair || undefined"
    @click="outside"
    @close="emit('close')"
  >
    <p class="viewer__title mono">{{ title }}</p>
    <div v-if="pair" class="viewer__pair" :style="{ width: pairWidth }">
      <img
        v-for="(one, index) in images"
        :key="one.src"
        class="viewer__side"
        :style="{ flexGrow: ratios[index] }"
        :src="one.src"
        :alt="one.name"
        @load="loaded(index, $event)"
      />
    </div>
    <div v-else-if="shown" ref="frame" class="viewer__frame">
      <img
        ref="image"
        :key="shown.src"
        class="viewer__image"
        :src="shown.src"
        :alt="shown.name"
        @load="measure"
        @click="toggle"
      />
    </div>
  </dialog>
</template>
