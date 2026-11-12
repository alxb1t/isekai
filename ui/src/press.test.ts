import { expect } from 'vitest'
import { cursorOf, gestureOf } from './press'
import { spec } from './test/spec'

spec('ui:panel:shift-places-and-a-plain-press-pans', () => {
  expect(gestureOf(true, null)).toBe('place')
  expect(gestureOf(false, 2)).toBe('move')
  expect(gestureOf(false, null)).toBe('pan')
  // Shift wins over a point under the pointer: it places, never moves.
  expect(gestureOf(true, 2)).toBe('place')
  // The first point is index 0, a point all the same.
  expect(gestureOf(false, 0)).toBe('move')
})

spec('ui:panel:the-cursor-follows-shift-and-the-pan', () => {
  expect(cursorOf(true, false)).toBe('crosshair')
  expect(cursorOf(false, false)).toBe('grab')
  expect(cursorOf(false, true)).toBe('grabbing')
  // A pan or a move under way is the grabbing hand whatever Shift says.
  expect(cursorOf(true, true)).toBe('grabbing')
})
