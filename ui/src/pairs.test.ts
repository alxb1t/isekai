import { expect } from 'vitest'
import {
  type Pairs,
  chosen,
  clicked,
  cleared,
  complete,
  deleted,
  forward,
  held,
  lone,
  moved,
  none,
  selected,
  undone,
} from './pairs'
import { spec } from './test/spec'
import type { Pair, Point } from './types'

const RADIUS = 8

/* Click `side` at `at` with the radius on screen at zoom 1. */
const click = (state: Pairs, side: 'a' | 'b', at: Point, scale = 1): Pairs =>
  clicked(state, side, at, scale, RADIUS)

/* `count` complete pairs, spread so no two points lie within the radius. */
function stand(count: number): Pairs {
  const pairs: Pair[] = Array.from({ length: count }, (_, n): Pair => [
    [100 * n, 10],
    [100 * n, 500],
  ])
  return held(pairs)
}

spec('ui:pairs:a-click-places-a-point-and-the-other-image-waits', () => {
  const state = click(none, 'a', [30, 40])

  expect(state.slots).toEqual([{ a: [30, 40], b: null }])
  expect(lone(state)).toEqual({ index: 0, has: 'a', waiting: 'b' })
  expect(complete(state)).toEqual([])
  // Either image may go first.
  expect(lone(click(none, 'b', [5, 6]))).toEqual({ index: 0, has: 'b', waiting: 'a' })
})

spec('ui:pairs:a-click-on-the-waiting-image-completes-the-pair', () => {
  const state = click(click(none, 'a', [30, 40]), 'b', [300, 400])

  expect(state.slots).toEqual([{ a: [30, 40], b: [300, 400] }])
  expect(lone(state)).toBeNull()
  expect(complete(state)).toEqual([[[30, 40], [300, 400]]])
  // The next click starts a new pair.
  expect(click(state, 'a', [60, 60]).slots).toHaveLength(2)
})

spec('ui:pairs:a-click-on-the-image-that-holds-the-lone-point-moves-it', () => {
  const state = click(click(none, 'a', [30, 40]), 'a', [200, 200])

  expect(state.slots).toEqual([{ a: [200, 200], b: null }])
  expect(lone(state)?.waiting).toBe('b')
})

spec('ui:pairs:a-click-near-a-point-selects-its-pair', () => {
  const state = stand(3)

  const near = click(state, 'a', [203, 12])

  expect(near.selected).toBe(2)
  expect(near.slots).toHaveLength(3)
  expect(near.past).toHaveLength(0)
  // A selection is no change: the same click again leaves the state as it was.
  expect(click(near, 'a', [203, 12])).toBe(near)
  // A click on the other image, away from any point of it, places a point there.
  expect(click(state, 'a', [150, 300]).slots).toHaveLength(4)
  // A row of the list selects its pair as a click on its point does, and none is held.
  expect(chosen(state, 1).selected).toBe(1)
  expect(chosen(state, 7)).toBe(state)
  expect(chosen(near, null).selected).toBeNull()
})

spec('ui:pairs:the-radius-is-the-same-on-screen-at-every-zoom', () => {
  const state = stand(1)

  // Eight screen pixels from the point: 8 image pixels at zoom 1, 2 at zoom 4.
  expect(selected(state, 'a', [8, 10], 1, RADIUS)).toBe(0)
  expect(selected(state, 'a', [2, 10], 4, RADIUS)).toBe(0)
  // One screen pixel past it at each.
  expect(selected(state, 'a', [9.5, 10], 1, RADIUS)).toBeNull()
  expect(selected(state, 'a', [2.5, 10], 4, RADIUS)).toBeNull()
  // Zoomed in, a click 8 image pixels away is a new point, not a selection.
  expect(click(state, 'a', [8, 10], 4).slots).toHaveLength(2)
})

spec('ui:pairs:a-drag-moves-a-point', () => {
  const state = stand(2)

  const dragged = moved(state, 1, 'b', [120, 480])

  expect(dragged.slots[1]).toEqual({ a: [100, 10], b: [120, 480] })
  expect(dragged.slots[0]).toEqual(state.slots[0])
  // A drag is one change: only its first move is a step of history.
  const longer = moved(dragged, 1, 'b', [130, 470], false)
  expect(longer.past).toHaveLength(dragged.past.length)
  expect(undone(longer).slots).toEqual(state.slots)
  // A pair that is not there, and a side with no point, move nothing.
  expect(moved(state, 9, 'a', [1, 1])).toBe(state)
  expect(moved(click(none, 'a', [3, 3]), 0, 'b', [1, 1]).slots[0].b).toBeNull()
})

spec('ui:pairs:a-delete-renumbers-the-later-pairs', () => {
  const state = click(stand(4), 'a', [100, 10])
  expect(state.selected).toBe(1)

  const after = deleted(state)

  expect(after.slots).toHaveLength(3)
  expect(after.slots.map((slot) => slot.a?.[0])).toEqual([0, 200, 300])
  expect(after.selected).toBeNull()
  // With nothing selected a delete changes nothing.
  expect(deleted(after)).toBe(after)
})

spec('ui:pairs:undo-and-clear', () => {
  const placed = click(click(none, 'a', [10, 10]), 'b', [500, 500])
  const dragged = moved(placed, 0, 'a', [40, 40])
  const selecting = click(dragged, 'a', [40, 40])
  const gone = deleted(selecting)

  expect(undone(gone).slots).toEqual(dragged.slots)
  // Selecting is no change, so the second undo restores the state before the drag.
  expect(undone(undone(gone)).slots).toEqual(placed.slots)
  expect(undone(dragged).slots).toEqual(placed.slots)
  expect(undone(undone(dragged)).slots).toHaveLength(1)
  expect(undone(undone(undone(dragged))).slots).toEqual([])
  // Nothing to undo leaves the state as it was.
  expect(undone(none)).toBe(none)

  const wiped = cleared(stand(5))
  expect(wiped.slots).toEqual([])
  expect(undone(wiped).slots).toHaveLength(5)
  expect(cleared(none)).toBe(none)
})

spec('ui:pairs:there-is-no-maximum', () => {
  let state: Pairs = none
  for (let n = 0; n < 40; n++) {
    state = click(click(state, 'a', [20 * n, 10]), 'b', [20 * n, 900])
  }

  expect(complete(state)).toHaveLength(40)
  expect(lone(state)).toBeNull()
})

spec('ui:pairs:forward-waits-for-the-floor-and-says-why', () => {
  expect(forward(stand(2), 6)).toBe('6 pairs needed · 2 placed')
  expect(forward(stand(6), 6)).toBeNull()
  const seventh = click(stand(6), 'a', [700, 10])

  expect(forward(seventh, 6)).toBe('point 7 has no match')
  expect(forward(click(seventh, 'b', [700, 500]), 6)).toBeNull()
  expect(forward(none, 3)).toBe('3 pairs needed · 0 placed')
})

spec('ui:pairs:the-pairs-stay-across-steps', () => {
  // The state is plain data: holding it again is the same pairs, and a copy of it too.
  const state = click(click(none, 'a', [10, 10]), 'b', [500, 500])
  const again = held(complete(state))

  expect(complete(again)).toEqual(complete(state))
  expect(complete(state)).toEqual([[[10, 10], [500, 500]]])
})
