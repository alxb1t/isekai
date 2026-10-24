<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useKeys } from '../composables/useKeys'
import { useViewer } from '../composables/useViewer'
import { plain } from '../stores/keys'

/* Images in a native dialog, fitted to the window. A click on the image toggles
   1:1 pixels, scrolled inside the dialog; `←` `→` `h` `l` step through the images,
   `↵` runs `open` on the shown one where it is given, and Esc or a click outside
   closes. With `pair`, every image stands side by side at one height, fit only.
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
  open?: (index: number) => void
}>()

const emit = defineEmits<{ close: [] }>()

const dialog = ref<HTMLDialogElement | null>(null)
const image = ref<HTMLImageElement | null>(null)
const { at, shown, step } = useViewer(() => props.images, props.start ?? 0, () => emit('close'))
const actual = ref(false)
/* The fitted image's scale, measured once it has loaded, on every resize while
   fitted, and on the switch back to fit: at 1:1 the drawn width is the natural one. */
const scale = ref<number | null>(null)

function measure(): void {
  const held = image.value
  if (held && held.naturalWidth > 0 && !actual.value)
    scale.value = Math.round((held.clientWidth / held.naturalWidth) * 100)
}

function toggle(): void {
  actual.value = !actual.value
  if (!actual.value) void nextTick(measure)
}

/* Each selected image opens fitted, even when a removed image's neighbour takes its place. */
watch(
  () => shown.value?.src,
  () => {
    actual.value = false
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

/* The pair's aspect ratios, each the image's own once it loads: widths in
   proportion to them put both at one height. */
const ratios = ref(props.images.map((one) => (one.width && one.height ? one.width / one.height : 1)))

function loaded(index: number, event: Event): void {
  const held = event.target as HTMLImageElement
  if (held.naturalHeight) ratios.value[index] = held.naturalWidth / held.naturalHeight
}

/* As wide as the window allows, and no taller than it. */
const pairWidth = computed(() => {
  const sum = ratios.value.reduce((total, one) => total + one, 0)
  return `min(calc(100vw - 64px), calc((100vh - 120px) * ${sum}))`
})

/* The dialog itself is the backdrop's target: a click on an image or the title
   lands on them instead. */
function outside(event: MouseEvent): void {
  if (event.target === dialog.value) dialog.value?.close()
}

const stepping = () => !props.pair && props.images.length > 1

useKeys('overlay', [
  { id: 'close', keys: plain('Escape'), label: 'close', run: () => dialog.value?.close() },
  {
    id: 'previous',
    keys: plain('ArrowLeft', 'KeyH'),
    label: 'previous',
    run: () => step(-1),
    when: stepping,
  },
  { id: 'next', keys: plain('ArrowRight', 'KeyL'), label: 'next', run: () => step(1), when: stepping },
  {
    id: 'open',
    keys: plain('Enter'),
    label: 'large view',
    run: () => props.open?.(at.value),
    when: () => props.open !== undefined,
  },
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
    <div v-else-if="shown" class="viewer__frame">
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
