import type { Pair, Point } from './types'

/* The pair editor, over an immutable state with its history. A pair holds a point on each
   of two images, `a` and `b`; a pair with one side is lone, and the image that lacks its
   match is the waiting image. Every function returns a new state and leaves its argument
   as it was. */

export type Side = 'a' | 'b'

export interface Slot {
  a: Point | null
  b: Point | null
}

interface Held {
  slots: readonly Slot[]
  selected: number | null
}

export interface Pairs extends Held {
  past: readonly Held[]
}

/* The pair that holds a point alone: its 0-based index, the side that has the point and the
   side that waits for its match. */
export interface Lone {
  index: number
  has: Side
  waiting: Side
}

export const none: Pairs = { slots: [], selected: null, past: [] }

const other = (side: Side): Side => (side === 'a' ? 'b' : 'a')

/** Return the editor holding `pairs`, every one complete and nothing to undo. */
export function held(pairs: readonly Pair[]): Pairs {
  return {
    slots: pairs.map(([a, b]): Slot => ({ a: [a[0], a[1]], b: [b[0], b[1]] })),
    selected: null,
    past: [],
  }
}

/** Return the complete pairs, in order. A lone point is left out. */
export function complete(state: Pairs): Pair[] {
  const done: Pair[] = []
  for (const { a, b } of state.slots) if (a && b) done.push([a, b])
  return done
}

/** Return the lone pair, or null when every pair is complete. */
export function lone(state: Pairs): Lone | null {
  const index = state.slots.findIndex((slot) => (slot.a === null) !== (slot.b === null))
  if (index < 0) return null
  const has: Side = state.slots[index].a ? 'a' : 'b'
  return { index, has, waiting: other(has) }
}

function changed(state: Pairs, next: Held): Pairs {
  return { ...next, past: [...state.past, { slots: state.slots, selected: state.selected }] }
}

/** Return the index of the pair with a point of `side` within `radius` screen pixels of `at`
    at `scale`, the nearest, else null. The radius is the same on screen at every zoom.
    e.g. radius 8 at scale 2 -> a point 4 image pixels away is selected */
export function selected(
  state: Pairs,
  side: Side,
  at: Point,
  scale: number,
  radius: number,
): number | null {
  let found: number | null = null
  let least = radius / scale
  state.slots.forEach((slot, index) => {
    const point = slot[side]
    if (!point) return
    const gap = Math.hypot(point[0] - at[0], point[1] - at[1])
    if (gap <= least) {
      least = gap
      found = index
    }
  })
  return found
}

/** Return the state with pair `index` selected, as a click on its row does; no change. */
export function chosen(state: Pairs, index: number | null): Pairs {
  if (index !== null && (index < 0 || index >= state.slots.length)) return state
  return index === state.selected ? state : { ...state, selected: index }
}

/** Return the state after a click on `side` at the image point `at`.
    A click within the radius of a point selects its pair; else it completes the lone pair
    from the waiting image, moves the lone point from the image that holds it, or places the
    next point on this image with the other image waiting. */
export function clicked(
  state: Pairs,
  side: Side,
  at: Point,
  scale: number,
  radius: number,
): Pairs {
  const near = selected(state, side, at, scale, radius)
  if (near !== null) return near === state.selected ? state : { ...state, selected: near }
  const alone = lone(state)
  const slots = state.slots.map((slot) => ({ ...slot }))
  if (alone === null) {
    slots.push(side === 'a' ? { a: at, b: null } : { a: null, b: at })
    return changed(state, { slots, selected: null })
  }
  slots[alone.index][side] = at
  return changed(state, { slots, selected: null })
}

/** Return the state with the `side` point of pair `index` at `to`. A drag is one change:
    pass `fresh` false for each move after its first. */
export function moved(
  state: Pairs,
  index: number,
  side: Side,
  to: Point,
  fresh = true,
): Pairs {
  if (index < 0 || index >= state.slots.length || !state.slots[index][side]) return state
  const slots = state.slots.map((slot, at): Slot => {
    if (at !== index) return slot
    return side === 'a' ? { a: to, b: slot.b } : { a: slot.a, b: to }
  })
  const next = { slots, selected: index }
  return fresh ? changed(state, next) : { ...next, past: state.past }
}

/** Return the state without the selected pair, the later pairs renumbered by their place.
    e.g. pairs 1..4 with 2 selected -> pairs 1..3, the old 3 and 4 now 2 and 3 */
export function deleted(state: Pairs): Pairs {
  if (state.selected === null) return state
  const slots = state.slots.filter((_, index) => index !== state.selected)
  return changed(state, { slots, selected: null })
}

/** Return the state as it was before its last change; unchanged with nothing to undo. */
export function undone(state: Pairs): Pairs {
  const last = state.past[state.past.length - 1]
  if (!last) return state
  return { slots: last.slots, selected: last.selected, past: state.past.slice(0, -1) }
}

/** Return the state with no pair, as a change that can be undone. */
export function cleared(state: Pairs): Pairs {
  return state.slots.length === 0 ? state : changed(state, { slots: [], selected: null })
}

/** Return why a stage waits, or null when it may go forward: a lone point has no match, or
    the floor of pairs is not placed.
    e.g. 2 pairs against 6 -> "6 pairs needed · 2 placed"; a lone seventh -> "point 7 has no match" */
export function forward(state: Pairs, floor: number): string | null {
  const alone = lone(state)
  if (alone !== null) return `point ${alone.index + 1} has no match`
  const count = complete(state).length
  return count < floor ? `${floor} pairs needed · ${count} placed` : null
}
