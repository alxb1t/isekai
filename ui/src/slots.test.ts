import { expect } from 'vitest'
import { fewer, more, renders, set, slots } from './slots'
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
  expect(set(held, 0, '')).toEqual([null, null, null, null])
  expect(renders(['144', null, '7', null])).toEqual({ count: 4, seeds: ['144', '7'] })
})
