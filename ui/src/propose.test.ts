import { expect } from 'vitest'
import { arrived, clicked, held, none } from './pairs'
import { answered, asked, due, keyOf, noAsks, pointsOf, refused, view } from './propose'
import { spec } from './test/spec'
import type { Outline, Pair } from './types'

const KEY = keyOf('bow', 'v1', '7')

const outline: Outline = {
  points: [[10, 20], [300, 40], [200, 400]],
  closed: true,
  white: 1,
  neutral: false,
  depth: 1,
}

const pair = (n: number): Pair => [[n * 50, 10], [n * 50, 400]]

spec('ui:proposal:a-stage-with-no-pairs-asks-once', () => {
  expect(due('two-stage', none, noAsks, KEY)).toBe(true)
  expect(due('cut', none, noAsks, KEY)).toBe(true)

  // Once asked, and after the answer, the same tattoo and render are not due again.
  const asking = asked(noAsks, KEY)
  expect(due('two-stage', none, asking, KEY)).toBe(false)
  expect(due('two-stage', none, answered(asking, KEY, 4), KEY)).toBe(false)
  expect(due('two-stage', none, refused(asking, KEY, 'no proposer'), KEY)).toBe(false)
  // Another render of the tattoo is its own ask.
  expect(due('two-stage', none, asking, keyOf('bow', 'v1', '8'))).toBe(true)
})

spec('ui:proposal:a-stage-with-pairs-asks-nothing', () => {
  expect(due('two-stage', held([pair(0)]), noAsks, KEY)).toBe(false)
  expect(due('cut', clicked(none, 'a', [5, 5], 1, 8), noAsks, KEY)).toBe(false)
  expect(due('two-stage', arrived(none, [pair(0)]), noAsks, KEY)).toBe(false)
})

spec('ui:proposal:the-direct-stage-asks-nothing', () => {
  expect(due('direct', none, noAsks, KEY)).toBe(false)
  expect(due(null, none, noAsks, KEY)).toBe(false)
  expect(pointsOf('direct', [pair(0)], outline)).toEqual([])
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

spec('ui:proposal:a-refusal-shows-its-words-and-the-clicks-still-work', () => {
  const words = 'the placement models are absent; run: uv run python -m isekai.boundary.unpack fetch config/placement.json'
  const asks = refused(asked(noAsks, KEY), KEY, words)

  expect(view(asks, KEY)).toBe(words)
  // The editor takes the click as ever: a refusal changes no pair.
  expect(clicked(none, 'a', [30, 40], 1, 8).slots).toEqual([{ a: [30, 40], b: null }])
  expect(due('two-stage', none, asks, KEY)).toBe(false)
})

spec('ui:proposal:an-empty-answer-says-so', () => {
  const asks = answered(asked(noAsks, KEY), KEY, 0)

  expect(view(asks, KEY)).toBe('Nothing proposed — place the pairs by clicking')
  expect(arrived(none, [])).toBe(none)
})
