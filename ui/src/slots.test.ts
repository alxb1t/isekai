import { expect } from 'vitest'
import { fewer, more, nearest, renders, set, slots, stepFour } from './slots'
import { spec } from './test/spec'

spec('ui:review:each-image-has-a-slot', () => {
  const held = slots({ count: 4, seeds: ['144'] })
  expect(held).toEqual(['144', null, null, null])

  expect(fewer(held)).toEqual(['144', null, null])
  expect(fewer(['144', '7'])).toEqual(['144'])
  expect(fewer(['144'])).toEqual(['144'])
  expect(renders(more(['144']))).toEqual({ count: 2, seeds: ['144'] })

  expect(set(held, 2, '7')).toEqual(['144', null, '7', null])
  expect(set(held, 2, '144')).toBe('seed 144 is already in slot 1')
  expect(set(held, 2, '0144')).toBe('seed 144 is already in slot 1')
  expect(set(held, 2, '007')).toEqual(['144', null, '7', null])
  expect(set(held, 0, '')).toEqual([null, null, null, null])
  expect(renders(['144', null, '7', null])).toEqual({ count: 4, seeds: ['144', '7'] })
})

spec('ui:review:four-is-one-grid-for-the-keys', () => {
  // `−` `+`, then two slots.
  const two = [[true, true], [true], [true]]
  let step = stepFour(two, { row: 0, column: 0 }, 'column+', 0)
  expect(step.focus).toEqual({ row: 0, column: 1 })
  const seen = []
  for (const move of ['row+', 'row+', 'row-', 'row-'] as const) {
    step = stepFour(two, step.focus, move, step.kept)
    seen.push(step.focus)
  }
  // `+`, the first slot, the second, and back to `+`: the column is kept.
  expect(seen).toEqual([
    { row: 1, column: 0 },
    { row: 2, column: 0 },
    { row: 1, column: 0 },
    { row: 0, column: 1 },
  ])
  // Down to one image `−` disables: its focus passes to `+`, and `h` stays there.
  const one = [[false, true], [true]]
  expect(nearest(one[0], 0)).toBe(1)
  expect(stepFour(one, { row: 0, column: 1 }, 'column-', 1).focus).toEqual({ row: 0, column: 1 })
  expect(stepFour(one, { row: 1, column: 0 }, 'row-', 0).focus).toEqual({ row: 0, column: 1 })
})
