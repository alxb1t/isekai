import { computed, ref, watch } from 'vue'
import { clamp } from '../grid'
import { type Command, plain, shifted } from '../stores/keys'

/** How far one of `j` `k` `↓` `↑` scrolls an image at full size, in px. */
export const SCROLL = 120

/** Keep a viewer's selection by URL as its image list changes, and whether it shows full size. */
export function useViewer<T extends { src: string }>(
  images: () => T[],
  start: number,
  close: () => void,
) {
  const last = () => Math.max(0, images().length - 1)
  const at = ref(clamp(start, last()))
  const shown = computed(() => images()[at.value])
  const actual = ref(false)
  const step = (direction: -1 | 1) => {
    at.value = clamp(at.value + direction, last())
  }
  const toggle = () => {
    actual.value = !actual.value
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
  /* Each image shows fitted, even when a removed image's neighbour takes its place. */
  watch(
    () => shown.value?.src,
    () => {
      actual.value = false
    },
    { flush: 'sync' },
  )
  return { at, last, shown, step, actual, toggle }
}

/** Return the viewer's keys (D4): `↵` toggles full size, `j` `k` `↓` `↑` scroll at full size,
    `h` `l` `←` `→` step, `⇧↵` runs the opener's `open` where it is given, and Esc closes.

    A pair is fitted alone, so `↵` is not offered on one. */
export function viewerKeys(
  viewer: ReturnType<typeof useViewer>,
  dialog: {
    close: () => void
    scroll: (by: number) => void
    pair: () => boolean
    open?: () => void
  },
): Command[] {
  const stepping = () => !dialog.pair() && viewer.last() > 0
  const full = () => !dialog.pair() && viewer.actual.value
  return [
    { id: 'close', keys: plain('Escape'), label: 'close', run: dialog.close },
    {
      id: 'previous',
      keys: plain('ArrowLeft', 'KeyH'),
      label: 'previous',
      run: () => viewer.step(-1),
      when: stepping,
    },
    {
      id: 'next',
      keys: plain('ArrowRight', 'KeyL'),
      label: 'next',
      run: () => viewer.step(1),
      when: stepping,
    },
    {
      id: 'full-size',
      keys: plain('Enter'),
      label: 'full size',
      run: viewer.toggle,
      when: () => !dialog.pair(),
    },
    {
      id: 'scroll-down',
      keys: plain('KeyJ', 'ArrowDown'),
      label: 'scroll down',
      run: () => dialog.scroll(SCROLL),
      when: full,
    },
    {
      id: 'scroll-up',
      keys: plain('KeyK', 'ArrowUp'),
      label: 'scroll up',
      run: () => dialog.scroll(-SCROLL),
      when: full,
    },
    {
      id: 'open',
      keys: [shifted('Enter')],
      label: 'large view',
      run: () => dialog.open?.(),
      when: () => dialog.open !== undefined,
    },
  ]
}
