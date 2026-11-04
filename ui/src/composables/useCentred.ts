import { nextTick, watch } from 'vue'

/** Scroll what `find` returns into view, centred, once drawn, each time `key` changes. */
export function useCentred(key: () => unknown, find: () => Element | null | undefined): void {
  watch(key, () => void nextTick(() => find()?.scrollIntoView({ block: 'center' })))
}
