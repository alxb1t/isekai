import { onScopeDispose, ref } from 'vue'
import { inkUrl } from '../tattoos'
import type { Outline } from '../types'

/** What a cut's card reads: its held outline, and the ink view the server draws for it. */
export interface CutRead {
  outline: () => Promise<Outline>
  ink: (outline: Outline, signal: AbortSignal) => Promise<{ image: Blob }>
}

/** Return a cut card's outline and ink URL, and `load`, which reads them; the scope's end is the card's leaving. */
export function useCutInk(read: CutRead) {
  const outline = ref<Outline | null>(null)
  const ink = ref<string | null>(null)

  /* Leaving the card ends the ink request, and an answer that still lands makes no URL. */
  const asking = new AbortController()
  let gone = false

  async function load(): Promise<void> {
    try {
      const held = await read.outline()
      outline.value = held
      if (!held.closed) return
      const made = await read.ink(held, asking.signal)
      ink.value = inkUrl(made.image, () => gone)
    } catch {
      // The card keeps what it shows: the crop, or the whole photograph.
    }
  }

  onScopeDispose(() => {
    gone = true
    asking.abort()
    if (ink.value) URL.revokeObjectURL(ink.value)
  })

  return { outline, ink, load }
}
