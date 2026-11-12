import { onUnmounted, shallowRef } from 'vue'
import { placementPreview, type PreviewAsk } from '../api'
import { answered, asked, due, idle, previewable, refused } from '../preview'
import type { Preview } from '../types'

/* The live preview of one stage: a change asks the server for the warped ink a declared
   time later, the newest answer alone is drawn, and a refusal is shown with its fix. The
   schedule and the answers are `preview.ts`; this holds the timer and the request. */

export interface PreviewOptions {
  /* The ask for the stage as it stands, or null when there is none to make. */
  ask: () => PreviewAsk | null
  /* The complete pairs that stand, and the least a preview is asked with. */
  count: () => number
  floor: number
  /* The wait after the last change, in ms. */
  wait: number
  collection: string
  name: () => string
  /* The request, so a test passes its own. */
  request?: typeof placementPreview
}

export function usePreview(options: PreviewOptions) {
  const request = options.request ?? placementPreview
  const state = shallowRef(idle)
  let last: number | null = null
  let timer: ReturnType<typeof setTimeout> | undefined
  let asking: AbortController | null = null

  function release(): void {
    if (state.value.shown) URL.revokeObjectURL(state.value.shown.url)
  }

  async function send(): Promise<void> {
    const body = options.ask()
    if (!previewable(options.count(), options.floor) || body === null) {
      asking?.abort()
      release()
      state.value = idle
      return
    }
    asking?.abort()
    const mine = new AbortController()
    asking = mine
    const made = asked(state.value)
    state.value = made.state
    try {
      const got: Preview = await request(options.collection, options.name(), body, mine.signal)
      if (mine.signal.aborted || made.ask !== state.value.newest) return
      const before = state.value.shown
      const url = URL.createObjectURL(got.image)
      state.value = answered(state.value, made.ask, { url, box: got.box, white: got.white })
      if (before) URL.revokeObjectURL(before.url)
    } catch (reason) {
      if (mine.signal.aborted || made.ask !== state.value.newest) return
      release()
      state.value = refused(state.value, made.ask, (reason as Error).message)
    }
  }

  function tick(): void {
    timer = undefined
    const now = Date.now()
    if (due(last, now, options.wait)) {
      last = null
      void send()
    } else if (last !== null) {
      timer = setTimeout(tick, Math.max(0, options.wait - (now - last)))
    }
  }

  /** Note a change of the stage: its ask is made the wait after the last change. */
  function changed(): void {
    last = Date.now()
    if (timer === undefined) timer = setTimeout(tick, options.wait)
  }

  function stop(): void {
    clearTimeout(timer)
    timer = undefined
    last = null
    asking?.abort()
    release()
    state.value = idle
  }

  onUnmounted(stop)
  return { state, changed, stop }
}
