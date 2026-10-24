import { computed, ref, watch } from 'vue'
import { clamp } from '../grid'

/** Keep a viewer's selection by URL as its image list changes. */
export function useViewer<T extends { src: string }>(
  images: () => T[],
  start: number,
  close: () => void,
) {
  const last = () => Math.max(0, images().length - 1)
  const at = ref(clamp(start, last()))
  const shown = computed(() => images()[at.value])
  const step = (direction: -1 | 1) => {
    at.value = clamp(at.value + direction, last())
  }
  watch(
    () => images().map((one) => one.src),
    (found, before) => {
      const kept = found.indexOf(before[at.value])
      at.value = kept < 0 ? clamp(at.value, last()) : kept
      if (!found.length) close()
    },
    { flush: 'sync' },
  )
  return { at, shown, step }
}
