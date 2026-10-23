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
  /* The render stage refused a count, or the offer could not be read: the bar
     stays so its reason is on screen. */
  refused: boolean
  /* A render session running. */
  rendering: boolean
}

/** Return the bar a screen shows, or null for none. */
export function bar(state: BarState): Bar {
  if (state.preparing || state.changes > 0) return 'prepare'
  if (state.images > 0 || state.refused || state.rendering) return 'render'
  return null
}

/** Return the reasons the Render bar shows beside its button, each once.

    A hold, such as no key or a job running, disables Render whatever the batch;
    a refused count is shown beside it, so the refusal is never silent. */
export function reasons(disabled: string | null, refused: string | null): string[] {
  return [...new Set([disabled, refused])].filter((reason) => reason !== null)
}

/* The failed Prepares Discard dismissed in this page, by batch, start and message.
   A module's, not a hub's: a hub opened again would otherwise show one again. A
   reload or another tab starts with none, and shows the failure the slot holds. */
const dismissed = new Set<string>()

function named(slot: JobSlot): string {
  return JSON.stringify([slot.batch, slot.progress?.started ?? null, slot.message])
}

/** Return the message of `batch`'s failed Prepare the slot holds, or null once dismissed. */
export function failed(slot: JobSlot | null, batch: string): string | null {
  return slot?.kind === 'prepare' &&
    slot.state === 'failed' &&
    slot.batch === batch &&
    !dismissed.has(named(slot))
    ? slot.message
    : null
}

/** Dismiss `batch`'s failed Prepare `slot` holds, so no hub in this page shows it again. */
export function dismiss(slot: JobSlot | null, batch: string): void {
  if (slot?.kind === 'prepare' && slot.state === 'failed' && slot.batch === batch) {
    dismissed.add(named(slot))
  }
}
