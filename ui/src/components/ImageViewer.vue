<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useKeys } from '../composables/useKeys'
import { plain } from '../stores/keys'

/* One image in a native dialog, fitted to the window. A click on the image
   toggles 1:1 pixels, scrolled inside the dialog; Esc or a click outside closes.
   The dialog keeps the URL of the page beneath (design spec §1 rule 8). */
const props = defineProps<{
  src: string
  name: string
  width?: number | null
  height?: number | null
}>()

const emit = defineEmits<{ close: [] }>()

const dialog = ref<HTMLDialogElement | null>(null)
const image = ref<HTMLImageElement | null>(null)
const actual = ref(false)
/* The fitted image's scale, measured once it has loaded, on every resize while
   fitted, and on the switch back to fit: at 1:1 the drawn width is the natural one. */
const scale = ref<number | null>(null)

function measure(): void {
  const shown = image.value
  if (shown && shown.naturalWidth > 0 && !actual.value)
    scale.value = Math.round((shown.clientWidth / shown.naturalWidth) * 100)
}

function toggle(): void {
  actual.value = !actual.value
  if (!actual.value) void nextTick(measure)
}

const title = computed(() => {
  const size = props.width && props.height ? ` · ${props.width}×${props.height}` : ''
  const fit = actual.value ? '1:1' : scale.value === null ? 'fit' : `fit ${scale.value}%`
  return `${props.name}${size} · ${fit}`
})

/* The dialog itself is the backdrop's target: a click on the image or the title
   lands on them instead. */
function outside(event: MouseEvent): void {
  if (event.target === dialog.value) dialog.value?.close()
}

useKeys('overlay', [
  { id: 'close', keys: plain('Escape'), label: 'close', run: () => dialog.value?.close() },
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
    @click="outside"
    @close="emit('close')"
  >
    <p class="viewer__title mono">{{ title }}</p>
    <div class="viewer__frame">
      <img
        ref="image"
        class="viewer__image"
        :src="src"
        :alt="name"
        @load="measure"
        @click="toggle"
      />
    </div>
  </dialog>
</template>
