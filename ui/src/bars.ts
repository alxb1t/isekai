import type { JobSlot } from './types'

/* Which bar a hub or Renders shows: one forward action at a time (design spec
   J2). Changes waiting for Prepare take it first, then images short of their
   count, then a render running. */
export type Bar = 'prepare' | 'render' | null

export interface BarState {
  /* Assigned cells with no sheet yet. */
  changes: number
  /* A Prepare running for this batch, or its refusal still shown. */
  preparing: boolean
  /* Images short of their approvals' counts, as the render stage counts them. */
  images: number
  /* A render session running. */
  rendering: boolean
}

/** Return the bar a screen shows, or null for none. */
export function bar(state: BarState): Bar {
  if (state.preparing || state.changes > 0) return 'prepare'
  if (state.images > 0 || state.rendering) return 'render'
  return null
}

/** Return the message of `batch`'s failed Prepare the slot holds, or null. */
export function failed(slot: JobSlot | null, batch: string): string | null {
  return slot?.kind === 'prepare' && slot.state === 'failed' && slot.batch === batch
    ? slot.message
    : null
}
