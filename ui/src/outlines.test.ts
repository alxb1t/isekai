import { expect } from 'vitest'
import {
  type Kind,
  type Outlines,
  begun,
  closed,
  drawing,
  drawn,
  held,
  none,
  regions,
  rows,
  rulesOf,
  shapes,
  stopped,
} from './outlines'
import { added, closed as closedDraft, drafted } from './polygon'
import { spec } from './test/spec'
import type { Point, TattooLimits } from './types'

const LIMITS = { region_min: 3, outline_max: 64 } as TattooLimits
const RULES = rulesOf(LIMITS, [1000, 800])

/* `count` points on a ring round (500, 400). */
const ring = (count: number): Point[] =>
  Array.from({ length: count }, (_, n): Point => [
    500 + 200 * Math.cos((2 * Math.PI * n) / count),
    400 + 200 * Math.sin((2 * Math.PI * n) / count),
  ])

/* Begin an outline, draw `count` points on it and close it. */
function outlined(state: Outlines, kind: Kind, count: number, index?: number): Outlines {
  const begin = begun(state, kind, index)
  return closed(drawn(begin, drafted(ring(count), true)))
}

spec('ui:render-stage:one-limb-and-any-number-of-exclusions', () => {
  let state = outlined(none, 'limb', 9)
  const first = state.limb

  // A second limb is the first drawn again, not another.
  state = begun(state, 'limb')
  expect(state.limb).toBe(first)
  expect(state.active).toEqual({ kind: 'limb', index: 0 })
  state = closed(state)
  expect(state.active).toBeNull()

  for (const count of [8, 6, 5]) state = outlined(state, 'exclusion', count)
  expect(state.exclusions).toHaveLength(3)
  expect(rows(state).map((row) => row.title)).toEqual(['limb', 'exclusion 1', 'exclusion 2', 'exclusion 3'])

  // An exclusion is edited by its row's index; nothing is added.
  const again = begun(state, 'exclusion', 1)
  expect(again.active).toEqual({ kind: 'exclusion', index: 1 })
  expect(again.exclusions).toHaveLength(3)
  // A new exclusion takes the one nobody has drawn on yet rather than a second.
  const blank = begun(state, 'exclusion')
  expect(blank.exclusions).toHaveLength(4)
  expect(begun(blank, 'exclusion').exclusions).toHaveLength(4)
})

spec('ui:render-stage:a-row-says-what-the-outline-does', () => {
  const state = outlined(outlined(none, 'limb', 9), 'exclusion', 8)

  expect(rows(state).map((row) => row.label)).toEqual(['9 points · keeps', '8 points · removes'])
  expect(rows(state).every((row) => !row.drawing)).toBe(true)
  // What is sent is each closed outline's points, the floor held by the rules it is closed by.
  expect(regions(state).limb).toHaveLength(9)
  expect(regions(state).exclusions.map((one) => one.length)).toEqual([8])
  expect(RULES.min).toBe(LIMITS.region_min)
})

spec('ui:render-stage:the-pairs-take-no-click-while-an-outline-is-drawn', () => {
  let state = begun(none, 'exclusion')
  expect(held(state)).toBe(true)
  expect(rows(state).map((row) => row.label)).toEqual(['drawing · 0 points'])

  // Clicks add points; the outline stays open under the floor, and the pairs stay held.
  let draft = drawing(state)!
  for (const at of ring(2)) draft = added(draft, at, RULES)
  state = closed(drawn(state, draft))
  expect(held(state)).toBe(true)
  expect(rows(state).map((row) => row.label)).toEqual(['drawing · 2 points'])
  expect(regions(state).exclusions).toEqual([])
  // Under the floor the draft does not close, so the drawing does not end.
  expect(closedDraft(draft, RULES)).toBe(draft)

  draft = added(draft, ring(3)[2], RULES)
  draft = closedDraft(draft, RULES)
  state = closed(drawn(state, draft))
  expect(held(state)).toBe(false)
  expect(rows(state).map((row) => row.label)).toEqual(['3 points · removes'])
  expect(regions(state).exclusions).toHaveLength(1)

  // With none drawn a draft is not taken, and an outline left open is listed as open.
  expect(drawn(state, draft)).toBe(state)
  const left = begun(state, 'limb')
  const open = drawn(left, drafted(ring(4), false))
  expect(rows(begun(open, 'exclusion', 0)).map((row) => row.label)).toEqual(['open · 4 points', 'drawing · 3 points'])
  expect(regions(open).limb).toBeNull()

  // Stopping lets the pairs take clicks again and leaves the outline as it stands.
  const stop = stopped(begun(open, 'limb'))
  expect(held(stop)).toBe(false)
  expect(shapes(stop).map((shape) => [shape.kind, shape.points.length, shape.closed, shape.drawing])).toEqual([
    ['limb', 4, false, false],
    ['exclusion', 3, true, false],
  ])
  expect(stopped(stop)).toBe(stop)
})
