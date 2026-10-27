import type { JobSlot } from './types'

/* Which bar a hub or Renders shows: one forward action at a time (design spec
   J2). Changes waiting for Prepare take it first, then a session running with its
   totals, then images short of their count, then a render running. */
export type Bar = 'prepare' | 'session' | 'render' | null

/* A running session's plan: the images it renders, and how many have landed. */
export interface Plan {
  of: number
  done: number
}

export interface BarState {
  /* Assigned cells with no sheet yet. */
  changes: number
  /* A Prepare running for this collection, or its refusal still shown. */
  preparing: boolean
  /* Images short of their approvals' counts, as the render stage counts them. */
  images: number
  /* The render stage refused a count, or the offer could not be read: the bar
     stays so its reason is on screen. */
  refused: boolean
  /* A render session running for this collection, not another's. */
  rendering: boolean
  /* The plan of the session this surface runs, for any collection, or null. */
  plan: Plan | null
}

/** Return the bar a screen shows, or null for none. */
export function bar(state: BarState): Bar {
  if (state.preparing || state.changes > 0) return 'prepare'
  if (state.plan !== null) return 'session'
  if (state.images > 0 || state.refused || state.rendering) return 'render'
  return null
}

/** Return the plan of the render `slot` runs, or null when it runs none. */
export function planOf(slot: JobSlot | null): Plan | null {
  const session = slot?.kind === 'render' && slot.state === 'running' ? slot.session : undefined
  return session ? { of: session.of, done: session.images.length } : null
}

/** Return the line naming the images short that the running session does not render, or null.

    `images` still counts the plan's images until each lands, so they are taken off.
    e.g. 4 short, a plan of 3 with none landed -> "1 image waits for the next session" */
export function waiting(state: Pick<BarState, 'images' | 'plan'>): string | null {
  const plan = state.plan
  const left = plan ? Math.max(0, state.images - (plan.of - plan.done)) : 0
  if (left === 0) return null
  return left === 1
    ? '1 image waits for the next session'
    : `${left} images wait for the next session`
}

/** Return the reasons the Render bar shows beside its button, each once.

    A hold, such as no key or a render running, disables Render whatever the collection;
    a refused count is shown beside it, so the refusal is never silent. */
export function reasons(disabled: string | null, refused: string | null): string[] {
  return [...new Set([disabled, refused])].filter((reason) => reason !== null)
}

/** Return why `collection`'s Prepare is disabled, or null: one Prepare runs at a time,
    so another collection's running Prepare holds it (design spec rule 6). */
export function held(slot: JobSlot | null, collection: string): string | null {
  return slot?.kind === 'prepare' && slot.state === 'running' && slot.collection !== collection
    ? `Prepare is running on ${slot.collection}`
    : null
}

/* The failed Prepares Discard dismissed in this page, by collection, start and message.
   A module's, not a hub's: a hub opened again would otherwise show one again. A
   reload or another tab starts with none, and shows the failure Prepare's slot holds. */
const dismissed = new Set<string>()

function named(slot: JobSlot): string {
  return JSON.stringify([slot.collection, slot.progress?.started ?? null, slot.message])
}

/** Return the message of `collection`'s failed Prepare `slot` holds, or null once dismissed. */
export function failed(slot: JobSlot | null, collection: string): string | null {
  return slot?.kind === 'prepare' &&
    slot.state === 'failed' &&
    slot.collection === collection &&
    !dismissed.has(named(slot))
    ? slot.message
    : null
}

/** Dismiss `collection`'s failed Prepare `slot` holds, so no hub in this page shows it again. */
export function dismiss(slot: JobSlot | null, collection: string): void {
  if (slot?.kind === 'prepare' && slot.state === 'failed' && slot.collection === collection) {
    dismissed.add(named(slot))
  }
}
