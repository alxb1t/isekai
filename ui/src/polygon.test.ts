import { expect } from 'vitest'
import {
  RADIUS,
  added,
  blank,
  box,
  canClose,
  cleared,
  closed,
  closes,
  drafted,
  inserted,
  moved,
  placed,
  ready,
  redone,
  removed,
  undone,
  vertexAt,
  type Draft,
  type Rules,
} from './polygon'
import { spec } from './test/spec'
import type { Point } from './types'

const RULES: Rules = { min: 3, max: 5, width: 100, height: 100 }
const SQUARE: Point[] = [
  [10, 10],
  [90, 10],
  [90, 90],
  [10, 90],
]

/* Click each point in turn, as the panel does, then return the draft. */
function clicked(points: Point[], rules = RULES): Draft {
  return points.reduce((draft, at) => added(draft, at, rules), blank)
}

spec('ui:outline-edit:a-click-adds-a-vertex-and-the-first-closes', () => {
  const open = clicked(SQUARE.slice(0, 3))
  expect(open.points).toEqual(SQUARE.slice(0, 3))
  expect(open.closed).toBe(false)
  expect(closes(open, [11, 11], 1, RULES)).toBe(true)
  expect(closes(open, [50, 50], 1, RULES)).toBe(false)

  const shut = closed(open, RULES)
  expect(shut.closed).toBe(true)
  expect(shut.points).toEqual(open.points)
  // A closed outline takes no more vertices by click.
  expect(added(shut, [50, 50], RULES)).toBe(shut)
  expect(closes(shut, [11, 11], 1, RULES)).toBe(false)
  // Under the floor the first vertex does not close, and the outline stays open.
  const few = clicked(SQUARE.slice(0, 2))
  expect(closes(few, [10, 10], 1, RULES)).toBe(false)
  expect(closed(few, RULES)).toBe(few)
})

spec('ui:outline-edit:the-radius-is-the-same-on-screen', () => {
  const open = clicked(SQUARE.slice(0, 3))
  for (const scale of [0.25, 1, 4, 16]) {
    // RADIUS screen pixels from the first vertex is RADIUS / scale image pixels.
    const edge: Point = [10 + RADIUS / scale, 10]
    const beyond: Point = [10 + (RADIUS + 1) / scale, 10]
    expect(closes(open, edge, scale, RULES), `at ${scale}`).toBe(true)
    expect(closes(open, beyond, scale, RULES), `at ${scale}`).toBe(false)
  }
})

spec('ui:outline-edit:a-drag-moves-a-vertex', () => {
  const draft = clicked(SQUARE)
  const first = moved(draft, 1, [60, 20], RULES)
  expect(first.points).toEqual([SQUARE[0], [60, 20], SQUARE[2], SQUARE[3]])
  // Later moves of the same drag replace the position and add no step to undo.
  const dragged = moved(first, 1, [65, 25], RULES, false)
  expect(dragged.points[1]).toEqual([65, 25])
  expect(dragged.past).toHaveLength(first.past.length)
  expect(undone(dragged).points).toEqual(SQUARE)
  // A vertex is held to the image.
  expect(moved(draft, 0, [-5, 500], RULES).points[0]).toEqual([0, 100])
  // The vertex picked is the nearest within the radius, at the zoom.
  expect(vertexAt(draft, [12, 11], 1)).toBe(0)
  expect(vertexAt(draft, [12, 11], 0.1)).toBe(0)
  expect(vertexAt(draft, [50, 50], 1)).toBeNull()
})

spec('ui:outline-edit:a-shift-click-inserts-on-the-nearest-edge', () => {
  const shut = closed(clicked(SQUARE, { ...RULES, max: 8 }), RULES)
  const into = inserted(shut, [50, 6], { ...RULES, max: 8 })
  expect(into.points).toEqual([SQUARE[0], [50, 10], SQUARE[1], SQUARE[2], SQUARE[3]])
  // The edge that closes the outline takes one too, after its last vertex.
  const last = inserted(shut, [4, 50], { ...RULES, max: 8 })
  expect(last.points).toEqual([...SQUARE, [10, 50]])
  // An open outline has no closing edge.
  const open = clicked(SQUARE.slice(0, 3), { ...RULES, max: 8 })
  expect(inserted(open, [4, 50], { ...RULES, max: 8 }).points).not.toContainEqual([10, 50])
  expect(inserted(blank, [4, 50], RULES)).toBe(blank)
})

spec('ui:outline-edit:a-double-click-removes-a-vertex', () => {
  const shut = closed(clicked(SQUARE.slice(0, 4), { ...RULES, max: 5 }), RULES)
  expect(ready(shut, RULES)).toBe(true)
  const four = removed(shut, 1, RULES)
  expect(four.points).toEqual([SQUARE[0], SQUARE[2], SQUARE[3]])
  expect(ready(four, RULES)).toBe(true)
  const fewer = removed(four, 0, RULES)
  expect(fewer.points).toHaveLength(2)
  expect(ready(fewer, RULES)).toBe(false)
  // Under the floor the outline opens, so what is saved is never a closed outline too small.
  expect(fewer.closed).toBe(false)
})

spec('ui:outline-edit:undo-and-clear', () => {
  const start = clicked(SQUARE.slice(0, 3))
  const addedOne = added(start, [50, 50], RULES)
  const movedOne = moved(addedOne, 0, [20, 20], RULES)
  const removedOne = removed(movedOne, 1, RULES)

  const back = undone(undone(undone(removedOne)))
  expect(back.points).toEqual(start.points)
  expect(undone(removedOne).points).toEqual(movedOne.points)
  expect(undone(undone(removedOne)).points).toEqual(addedOne.points)
  expect(undone(start).points).toEqual(SQUARE.slice(0, 2))

  const wiped = cleared(movedOne)
  expect(wiped.points).toEqual([])
  expect(wiped.closed).toBe(false)
  expect(undone(wiped).points).toEqual(movedOne.points)
  expect(undone(blank)).toBe(blank)
  expect(cleared(blank)).toBe(blank)
  // A change leaves the draft it came from as it was.
  const frozen = Object.freeze(drafted(SQUARE, true))
  expect(() => removed(frozen, 0, RULES)).not.toThrow()
  expect(frozen.points).toEqual(SQUARE)
  expect(box(drafted(SQUARE, true))).toEqual({ x: 10, y: 10, width: 80, height: 80 })
  expect(box(blank)).toBeNull()
})

spec('ui:outline-edit:the-ceiling-is-held', () => {
  const full = clicked([[1, 1], [2, 2], [3, 3], [4, 4], [5, 5]])
  expect(full.points).toHaveLength(RULES.max)
  expect(added(full, [6, 6], RULES)).toBe(full)
  const shut = closed(full, RULES)
  expect(inserted(shut, [3, 2], RULES)).toBe(shut)
  expect(ready(shut, RULES)).toBe(true)
  // A click off the image adds nothing.
  expect(added(blank, [101, 5], RULES)).toBe(blank)
})

spec('ui:outline-edit:a-shift-click-places-by-where-it-lands', () => {
  const open = clicked(SQUARE.slice(0, 3))

  // The first vertex closes an outline that can close, and adds nothing.
  const shut = placed(open, [12, 11], 1, RULES)
  expect(shut.closed).toBe(true)
  expect(shut.points).toEqual(open.points)
  // Another vertex changes nothing.
  expect(placed(open, [91, 89], 1, RULES)).toBe(open)
  // An edge within the radius takes a vertex on it, after the edge's first end.
  expect(placed(open, [50, 14], 1, RULES).points).toEqual([SQUARE[0], [50, 10], SQUARE[1], SQUARE[2]])
  // Bare image adds a vertex at the click.
  const more = placed(open, [40, 60], 1, RULES)
  expect(more.points).toEqual([...open.points, [40, 60]])
  expect(more.closed).toBe(false)
  // The radius is on screen: 4 image pixels from an edge is 16 screen pixels at zoom 4.
  expect(placed(open, [50, 14], 4, RULES).points).toEqual([...open.points, [50, 14]])

  // A closed outline takes a vertex on an edge, and nothing on its first vertex or bare image.
  expect(placed(shut, [50, 14], 1, RULES).points).toEqual([SQUARE[0], [50, 10], SQUARE[1], SQUARE[2]])
  expect(placed(shut, [11, 11], 1, RULES)).toBe(shut)
  expect(placed(shut, [40, 60], 1, RULES)).toBe(shut)
})

spec('ui:outline-edit:a-near-miss-never-adds-a-vertex', () => {
  // Below the floor the first vertex does not close, and a click by it adds no vertex under it.
  const below = clicked(SQUARE.slice(0, 2))
  expect(placed(below, [13, 12], 1, RULES)).toBe(below)
  // At the floor the same click a few image pixels off closes, and adds none.
  const atFloor = clicked(SQUARE.slice(0, 3))
  const shut = placed(atFloor, [13, 12], 1, RULES)
  expect(shut.closed).toBe(true)
  expect(shut.points).toHaveLength(3)
  // A near miss of any other vertex adds none either.
  expect(placed(atFloor, [88, 12], 1, RULES)).toBe(atFloor)
})

spec('ui:outline-edit:redo-restores-what-undo-took', () => {
  const start = clicked(SQUARE.slice(0, 3))
  const more = added(start, [50, 50], RULES)

  const back = undone(more)
  expect(back.future).toHaveLength(1)
  const again = redone(back)
  expect(again.points).toEqual(more.points)
  expect(again.past).toEqual(more.past)
  expect(again.future).toEqual([])
  // Every undo is redone, the last first.
  const shifted = moved(more, 0, [20, 20], RULES)
  const twice = undone(undone(shifted))
  expect(redone(twice).points).toEqual(more.points)
  expect(redone(redone(twice)).points).toEqual(shifted.points)
  // A new change after an undo leaves nothing to redo.
  const fresh = added(back, [60, 60], RULES)
  expect(fresh.future).toEqual([])
  expect(redone(fresh)).toBe(fresh)
  expect(cleared(back).future).toEqual([])
  // The later moves of a drag keep what is held, and nothing to redo leaves the draft as it was.
  expect(moved(back, 0, [30, 30], RULES, false).future).toEqual(back.future)
  expect(redone(blank)).toBe(blank)
  expect(blank.future).toEqual([])
  expect(drafted(SQUARE, true).future).toEqual([])
})

spec('ui:outline-edit:closing-needs-the-floor', () => {
  const fewer = clicked(SQUARE.slice(0, RULES.min - 1))
  expect(canClose(fewer, RULES)).toBe(false)
  expect(closed(fewer, RULES)).toBe(fewer)

  const atFloor = clicked(SQUARE.slice(0, RULES.min))
  expect(canClose(atFloor, RULES)).toBe(true)
  const shut = closed(atFloor, RULES)
  expect(shut.closed).toBe(true)
  // Closing it again leaves it closed, and a closed outline cannot close.
  expect(canClose(shut, RULES)).toBe(false)
  expect(closed(shut, RULES)).toBe(shut)
  expect(canClose(blank, RULES)).toBe(false)
})
