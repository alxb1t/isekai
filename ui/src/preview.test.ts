import { expect } from 'vitest'
import { type Answer, answered, asked, dimmed, due, idle, opacityOf, previewable, refused } from './preview'
import { spec } from './test/spec'

const answer = (url: string): Answer => ({
  url,
  box: { x: 1, y: 2, width: 30, height: 40 },
  white: 200,
})

spec('ui:preview:nothing-is-asked-below-the-floor', () => {
  expect(previewable(2, 3)).toBe(false)
  expect(previewable(0, 3)).toBe(false)
  expect(previewable(3, 3)).toBe(true)
  expect(previewable(12, 3)).toBe(true)
})

spec('ui:preview:one-ask-follows-a-burst-of-changes', () => {
  const wait = 1000
  // Three changes within the wait, at 0, 400 and 800 ms; the page keeps the last.
  let last: number | null = 0
  last = 400
  last = 800
  const asks: number[] = []
  for (let now = 0; now <= 3000; now += 100) {
    if (due(last, now, wait)) {
      asks.push(now)
      last = null
    }
  }

  expect(asks).toEqual([1800])
  expect(due(null, 5000, wait)).toBe(false)
  expect(due(800, 1799, wait)).toBe(false)
  expect(due(800, 1800, wait)).toBe(true)
})

spec('ui:preview:the-newest-answer-wins', () => {
  const first = asked(idle)
  const second = asked(first.state)

  const late = answered(second.state, first.ask, answer('old'))
  expect(late).toBe(second.state)
  expect(late.shown).toBeNull()
  expect(late.asking).toBe(true)

  const drawn = answered(second.state, second.ask, answer('new'))
  expect(drawn.shown?.url).toBe('new')
  expect(drawn.asking).toBe(false)
  // An older answer after the newer is dropped, and the newer stays drawn.
  expect(answered(drawn, first.ask, answer('old'))).toBe(drawn)
  expect(refused(drawn, first.ask, 'old refusal')).toBe(drawn)
})

spec('ui:preview:the-last-answer-is-dimmed-while-the-next-is-asked', () => {
  const drawn = answered(asked(idle).state, 1, answer('one'))
  expect(dimmed(drawn)).toBe(false)
  expect(opacityOf(drawn, 0.8)).toBe(0.8)

  const next = asked(drawn)

  expect(next.state.shown?.url).toBe('one')
  expect(dimmed(next.state)).toBe(true)
  expect(opacityOf(next.state, 0.8)).toBe(0.4)
  const after = answered(next.state, next.ask, answer('two'))
  expect(dimmed(after)).toBe(false)
  expect(after.shown?.url).toBe('two')
  // With nothing drawn there is nothing to dim.
  expect(dimmed(asked(idle).state)).toBe(false)
})

spec('ui:preview:a-refusal-clears-the-answer-and-shows-its-fix', () => {
  const drawn = answered(asked(idle).state, 1, answer('one'))
  const next = asked(drawn)

  const refusedNow = refused(next.state, next.ask, 'stage 1 holds 4 pairs and the render stage needs 6')

  expect(refusedNow.shown).toBeNull()
  expect(refusedNow.refusal).toBe('stage 1 holds 4 pairs and the render stage needs 6')
  expect(refusedNow.asking).toBe(false)
  // The next ask clears the words.
  expect(asked(refusedNow).state.refusal).toBeNull()
})
