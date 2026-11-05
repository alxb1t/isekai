import { expect } from 'vitest'
import { placement } from './placement'
import { spec } from './test/spec'

spec('ui:vocabulary:the-list-opens-above-near-the-foot', () => {
  expect(placement(300, 500, 300)).toBe('below')
  expect(placement(100, 400, 300)).toBe('above')
  expect(placement(120, 200, 300)).toBe('above')
  expect(placement(200, 120, 300)).toBe('below')
})
