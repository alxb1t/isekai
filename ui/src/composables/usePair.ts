import { computed, ref } from 'vue'

/** Return a pair's aspect ratios, a load handler measuring each, and the width
    that stands both at one height, as wide as `across` and no taller than `down`.

    Widths in proportion to the ratios put both at one height; a ratio is the
    image's own once it loads. e.g. usePair([1, 1], '100%', '(100vh - 200px)') */
export function usePair(initial: number[], across: string, down: string) {
  const ratios = ref(initial)

  function loaded(index: number, event: Event): void {
    const held = event.target as HTMLImageElement
    if (held.naturalHeight) ratios.value[index] = held.naturalWidth / held.naturalHeight
  }

  const width = computed(() => {
    const sum = ratios.value.reduce((total, one) => total + one, 0)
    return `min(${across}, calc(${down} * ${sum}))`
  })

  return { ratios, loaded, width }
}
