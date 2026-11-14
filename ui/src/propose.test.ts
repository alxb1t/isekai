import { expect } from 'vitest'
import { arrived, clicked, held, none } from './pairs'
import { answered, asked, due, keyOf, noAsks, pointsOf, refused, stands, view } from './propose'
import { spec } from './test/spec'
import type { Outline, Pair } from './types'

const KEY = keyOf('bow', 'v1', '7')
const POINTS = 3

const outline: Outline = {
  points: [[10, 20], [300, 40], [200, 400]],
  closed: true,
  white: 1,
  neutral: false,
  depth: 1,
}

const pair = (n: number): Pair => [[n * 50, 10], [n * 50, 400]]

spec('ui:proposal:a-stage-with-no-pairs-asks-once', () => {
  expect(due('two-stage', none, noAsks, KEY, POINTS, false)).toBe(true)
  expect(due('cut', none, noAsks, KEY, POINTS, false)).toBe(true)

  // Once asked, and after the answer, the same tattoo and render are not due again.
  const asking = asked(noAsks, KEY)
  expect(due('two-stage', none, asking, KEY, POINTS, false)).toBe(false)
  expect(due('two-stage', none, answered(asking, KEY, 4), KEY, POINTS, false)).toBe(false)
  expect(due('two-stage', none, refused(asking, KEY), KEY, POINTS, false)).toBe(false)
  // Another render of the tattoo is its own ask.
  expect(due('two-stage', none, asking, keyOf('bow', 'v1', '8'), POINTS, false)).toBe(true)

  // An answer belongs to the ask that made it: a later ask under the same key is not it,
  // and neither is an ask already answered.
  const mine = asking[KEY]
  expect(stands(asking, KEY, mine)).toBe(true)
  expect(stands(asked(asking, KEY), KEY, mine)).toBe(false)
  expect(stands(answered(asking, KEY, 4), KEY, mine)).toBe(false)
  expect(stands(noAsks, KEY, undefined)).toBe(false)
})

spec('ui:proposal:a-stage-with-pairs-asks-nothing', () => {
  expect(due('two-stage', held([pair(0)]), noAsks, KEY, POINTS, false)).toBe(false)
  expect(due('cut', clicked(none, 'a', [5, 5], 1, 8), noAsks, KEY, POINTS, false)).toBe(false)
  expect(due('two-stage', arrived(none, [pair(0)]), noAsks, KEY, POINTS, false)).toBe(false)
})

spec('ui:proposal:the-direct-stage-asks-nothing', () => {
  expect(due('direct', none, noAsks, KEY, POINTS, false)).toBe(false)
  expect(due(null, none, noAsks, KEY, POINTS, false)).toBe(false)
  expect(pointsOf('direct', [pair(0)], outline)).toEqual([])
})

spec('ui:proposal:an-ask-waits-for-the-saved-outline', () => {
  // A read or a save in flight holds the ask, which goes out once it has answered.
  expect(due('cut', none, noAsks, KEY, POINTS, true)).toBe(false)
  expect(due('cut', none, noAsks, KEY, POINTS, false)).toBe(true)

  // A tattoo with no point sends nothing, however the read stands.
  expect(due('cut', none, noAsks, KEY, 0, false)).toBe(false)
  expect(due('two-stage', none, noAsks, KEY, 0, false)).toBe(false)
  expect(pointsOf('cut', [], { ...outline, points: [] })).toEqual([])
})

spec('ui:proposal:the-points-sent-are-the-tattoos-on-the-photograph', () => {
  const stage1: Pair[] = [[[10, 20], [300, 400]], [[30, 40], [310, 420]]]

  // An upload sends the photograph side of its stage-1 pairs, never the tattoo's side.
  expect(pointsOf('two-stage', stage1, outline)).toEqual([[300, 400], [310, 420]])
  // A cut has no stage-1 pair: its outline is on the photograph.
  expect(pointsOf('cut', [], outline)).toEqual(outline.points)
})

spec('ui:proposal:the-page-shows-that-it-is-asking', () => {
  expect(view(noAsks, KEY)).toBeNull()

  const asking = asked(noAsks, KEY)
  expect(view(asking, KEY)).toBe('Proposing pairs…')
  expect(view(answered(asking, KEY, 4), KEY)).toBeNull()
  // The line is the render's own: another render shows none.
  expect(view(asking, keyOf('bow', 'v1', '8'))).toBeNull()
})

spec('ui:proposal:a-refusal-says-so-in-a-plain-line-and-the-clicks-still-work', () => {
  const asks = refused(asked(noAsks, KEY), KEY)

  expect(view(asks, KEY)).toBe('Could not propose pairs — place them by clicking')
  // The editor takes the click as ever: a refusal changes no pair.
  expect(clicked(none, 'a', [30, 40], 1, 8).slots).toEqual([{ a: [30, 40], b: null }])
  expect(due('two-stage', none, asks, KEY, POINTS, false)).toBe(false)
})

spec('ui:proposal:an-empty-answer-says-so', () => {
  const asks = answered(asked(noAsks, KEY), KEY, 0)

  expect(view(asks, KEY)).toBe('Nothing proposed — place the pairs by clicking')
  expect(arrived(none, [])).toBe(none)
})
