import { expect } from 'vitest'
import { asks, left, lone, type Stage } from './leave'
import { clicked, complete, held, none } from './pairs'
import { spec } from './test/spec'
import type { Pair, Point } from './types'

const pairs = (count: number): Pair[] =>
  Array.from({ length: count }, (_, n): Pair => [[n * 50, 10], [n * 50, 400]])

const click = (state: ReturnType<typeof held>, side: 'a' | 'b', at: Point) =>
  clicked(state, side, at, 1, 8)

const stage = (over: Partial<Stage> = {}): Stage => ({
  mode: 'two-stage',
  step: 'photo',
  pairs: held(pairs(7)),
  saved: null,
  ...over,
})

const withLone = (count: number, side: 'a' | 'b' = 'a') => click(held(pairs(count)), side, [900, 900])

spec('ui:leave:a-lone-point-asks-and-a-clean-stage-does-not', () => {
  expect(asks(stage({ pairs: withLone(7) }))).not.toBeNull()
  expect(asks(stage())).toBeNull()
  expect(asks(stage({ pairs: none }))).toBeNull()
  expect(lone(stage())).toBeNull()
  // A step that pairs no images has nothing to ask about.
  expect(asks(stage({ step: 'review', pairs: withLone(7) }))).toBeNull()
  expect(asks(stage({ step: 'outline', pairs: withLone(7) }))).toBeNull()
})

spec('ui:leave:the-dialog-names-the-point-and-its-missing-match', () => {
  // Point 8 lies on the tattoo of stage 1 and has no match on the photograph.
  const first = stage({ pairs: withLone(7), saved: new Date(2026, 10, 12, 14, 5) })
  expect(lone(first)).toEqual({ number: 8, on: 'tattoo', missing: 'photograph' })
  expect(asks(first)).toEqual({
    title: 'Point 8 has no match on the photograph',
    standing: '7 pairs stand',
    saved: 'saved 14:05',
  })
  // A lone point on the photograph waits for the tattoo.
  expect(asks(stage({ pairs: withLone(7, 'b') }))?.title).toBe('Point 8 has no match on the tattoo')

  // The later stage names its own images and says nothing of a save.
  const later = asks(stage({ step: 'render', pairs: withLone(1) }))
  expect(later).toEqual({ title: 'Point 2 has no match on the render', standing: '1 pair stands', saved: null })
  expect(asks(stage({ step: 'render', mode: 'direct', pairs: withLone(3, 'b') }))?.title).toBe(
    'Point 4 has no match on the tattoo',
  )
  // A first point alone leaves no pair standing, so there is nothing saved to name.
  expect(asks(stage({ pairs: withLone(0) }))).toEqual({
    title: 'Point 1 has no match on the photograph',
    standing: 'no pair stands',
    saved: null,
  })
  // Stage 1 read from disk and not saved since says only that it is saved.
  expect(asks(stage({ pairs: withLone(7) }))?.saved).toBe('saved')
})

spec('ui:leave:leaving-drops-the-lone-point-and-keeps-the-pairs', () => {
  const before = withLone(7)
  expect(before.slots).toHaveLength(8)

  const after = left(before)
  expect(after.slots).toHaveLength(7)
  expect(complete(after)).toEqual(pairs(7))
  expect(lone(stage({ pairs: after }))).toBeNull()
  // A state with no lone point is returned as it is.
  const clean = held(pairs(7))
  expect(left(clean)).toBe(clean)
})
