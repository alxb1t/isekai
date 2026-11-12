import { expect } from 'vitest'
import {
  type Pairs,
  accepted,
  acceptedAll,
  arrived,
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
  proposals,
  redone,
  selected,
  sent,
  touched,
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

spec('ui:pairs:a-plain-click-selects-and-places-nothing', () => {
  const state = stand(3)

  const near = touched(state, 'a', [203, 12], 1, RADIUS)
  expect(near.selected).toBe(2)
  expect(near.slots).toEqual(state.slots)
  expect(near.past).toHaveLength(0)
  // A selection is no change: the same click again leaves the state as it was.
  expect(touched(near, 'a', [203, 12], 1, RADIUS)).toBe(near)
  // Bare image places nothing and changes nothing.
  expect(touched(state, 'a', [150, 300], 1, RADIUS)).toBe(state)
  expect(touched(none, 'a', [150, 300], 1, RADIUS)).toBe(none)
  // The radius is on screen: 8 image pixels away is out of reach at zoom 4.
  expect(touched(state, 'a', [8, 10], 4, RADIUS)).toBe(state)
  // A lone point's pair is selected by its own image alone.
  const lonely = click(none, 'a', [30, 40])
  expect(touched(lonely, 'a', [31, 41], 1, RADIUS).selected).toBe(0)
  expect(touched(lonely, 'b', [31, 41], 1, RADIUS)).toBe(lonely)
})

spec('ui:pairs:redo-restores-what-undo-took', () => {
  const placed = click(click(none, 'a', [10, 10]), 'b', [500, 500])
  const dragged = moved(placed, 0, 'a', [40, 40])

  const back = undone(dragged)
  expect(back.future).toHaveLength(1)
  const again = redone(back)
  expect(again.slots).toEqual(dragged.slots)
  expect(again.selected).toBe(dragged.selected)
  expect(again.past).toEqual(dragged.past)
  expect(again.future).toEqual([])
  // Every undo is redone, the last first.
  const twice = undone(undone(dragged))
  expect(redone(twice).slots).toEqual(placed.slots)
  expect(redone(redone(twice)).slots).toEqual(dragged.slots)
  // A new change after an undo leaves nothing to redo; a selection is no change and keeps it.
  const fresh = click(back, 'a', [300, 300])
  expect(fresh.future).toEqual([])
  expect(redone(fresh)).toBe(fresh)
  expect(touched(back, 'a', [10, 10], 1, RADIUS).future).toEqual(back.future)
  // The later moves of a drag keep what is held, and nothing to redo leaves the state as it was.
  expect(moved(back, 0, 'a', [50, 50], false).future).toEqual(back.future)
  expect(redone(none)).toBe(none)
  // An arrival while an undo is held joins what redo brings back.
  const arrival = proposed(back, 2)
  const redoneArrival = redone(arrival)
  expect(redoneArrival.slots[0].a).toEqual([40, 40])
  expect(proposals(redoneArrival)).toHaveLength(2)
  expect(proposals(undone(redoneArrival))).toHaveLength(2)
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

/* `count` proposed pairs, spread as `stand` spreads them, after `before`. */
function proposed(before: Pairs, count: number): Pairs {
  const answer: Pair[] = Array.from({ length: count }, (_, n): Pair => [
    [1000 + 100 * n, 10],
    [1000 + 100 * n, 500],
  ])
  return arrived(before, answer)
}

spec('ui:proposal:proposed-pairs-arrive-numbered-after-the-held-ones', () => {
  const state = proposed(stand(2), 4)

  expect(state.slots).toHaveLength(6)
  expect(state.slots.map((slot) => slot.proposed === true)).toEqual([false, false, true, true, true, true])
  expect(state.slots.map((slot) => slot.a?.[0])).toEqual([0, 100, 1000, 1100, 1200, 1300])
  expect(proposals(state)).toEqual(state.slots.slice(2))
  // An ordinary slot carries no key at all, and the arrival is no change of the history.
  expect('proposed' in state.slots[0]).toBe(false)
  expect(state.past).toHaveLength(0)
  expect(arrived(state, [])).toBe(state)
})

spec('ui:proposal:accept-takes-the-selected-pair', () => {
  const state = click(proposed(none, 4), 'a', [1200, 10])
  expect(state.selected).toBe(2)

  const after = accepted(state)

  expect(after.slots[2]).toEqual({ a: [1200, 10], b: [1200, 500] })
  expect('proposed' in after.slots[2]).toBe(false)
  expect(proposals(after)).toHaveLength(3)
  expect(after.selected).toBe(2)
  // With no pair selected, or an ordinary one, an accept changes nothing.
  expect(accepted(proposed(none, 2))).toEqual(proposed(none, 2))
  expect(accepted(click(stand(1), 'a', [0, 10]))).toEqual(click(stand(1), 'a', [0, 10]))
})

spec('ui:proposal:accept-all-takes-every-pair', () => {
  const state = proposed(stand(1), 4)

  const after = acceptedAll(state)

  expect(after.slots).toHaveLength(5)
  expect(proposals(after)).toEqual([])
  expect(after.slots.every((slot) => !('proposed' in slot))).toBe(true)
  expect(complete(after)).toEqual(complete(state))
  // With none proposed it changes nothing.
  expect(acceptedAll(after)).toBe(after)
})

spec('ui:proposal:a-drag-accepts-the-pair-it-moves', () => {
  const state = proposed(none, 4)

  const dragged = moved(state, 1, 'b', [1120, 480])

  expect(dragged.slots[1]).toEqual({ a: [1100, 10], b: [1120, 480] })
  expect('proposed' in dragged.slots[1]).toBe(false)
  expect(proposals(dragged)).toHaveLength(3)
  // The rest of a drag keeps the pair ordinary.
  const longer = moved(dragged, 1, 'b', [1130, 470], false)
  expect(longer.slots[1].proposed).toBeUndefined()
  expect(proposals(longer)).toHaveLength(3)
})

spec('ui:proposal:undo-restores-a-proposed-pair', () => {
  const state = click(proposed(none, 4), 'a', [1200, 10])
  const after = accepted(state)

  const back = undone(after)

  expect(back.slots).toEqual(state.slots)
  expect(back.slots[2].proposed).toBe(true)
  // Accept all is one step, and undo gives every pair its mark again.
  expect(undone(acceptedAll(state)).slots).toEqual(state.slots)
})

spec('ui:proposal:undo-never-removes-the-arrival', () => {
  // A point is clicked while the ask is pending, then the answer arrives.
  const state = proposed(click(none, 'a', [10, 10]), 4)
  expect(state.slots).toHaveLength(5)

  const first = undone(state)
  const second = undone(first)

  expect(first.slots).toHaveLength(4)
  expect(proposals(first)).toHaveLength(4)
  expect(first.slots.map((slot) => slot.a?.[0])).toEqual([1000, 1100, 1200, 1300])
  expect(second).toBe(first)
  // Every older step of the history holds the arrival too.
  const placed = proposed(click(click(none, 'a', [10, 10]), 'b', [500, 500]), 4)
  const dragged = moved(placed, 0, 'a', [40, 40])
  expect(proposals(undone(dragged))).toHaveLength(4)
  expect(proposals(undone(undone(dragged)))).toHaveLength(4)
})

spec('ui:proposal:a-proposed-pair-is-sent-as-an-ordinary-pair', () => {
  const state = proposed(stand(1), 2)

  expect(sent(state)).toEqual([
    [[0, 10], [0, 500]],
    [[1000, 10], [1000, 500]],
    [[1100, 10], [1100, 500]],
  ])
  expect(JSON.stringify(sent(state))).not.toContain('proposed')
  // A lone point is left out, as `complete` leaves it.
  expect(sent(click(state, 'a', [5000, 5]))).toHaveLength(3)
})

spec('ui:proposal:a-deleted-proposed-pair-is-gone', () => {
  const state = click(proposed(none, 4), 'a', [1100, 10])
  expect(state.selected).toBe(1)

  const after = deleted(state)

  expect(after.slots).toHaveLength(3)
  expect(after.slots.map((slot) => slot.a?.[0])).toEqual([1000, 1200, 1300])
  expect(proposals(after)).toHaveLength(3)
})

spec('ui:proposal:forward-waits-while-a-pair-is-proposed-and-says-so', () => {
  const state = proposed(none, 4)

  // Before the floor and before the lone point.
  expect(forward(state, 8)).toBe('4 proposed · accept or delete them')
  expect(forward(click(state, 'a', [5000, 5]), 8)).toBe('4 proposed · accept or delete them')
  expect(forward(accepted(click(state, 'a', [1000, 10])), 8)).toBe('3 proposed · accept or delete them')
})

spec('ui:proposal:forward-goes-when-every-pair-is-accepted', () => {
  const state = proposed(none, 9)

  expect(forward(state, 8)).not.toBeNull()
  expect(forward(acceptedAll(state), 8)).toBeNull()
})
