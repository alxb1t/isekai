import { expect } from 'vitest'
import { cursorOf, endsPress, gestureOf } from './press'
import { spec } from './test/spec'

spec('ui:panel:shift-places-and-a-plain-press-pans', () => {
  expect(gestureOf(true, null)).toBe('place')
  expect(gestureOf(false, 2)).toBe('move')
  expect(gestureOf(false, null)).toBe('pan')
  // Shift wins over a point under the pointer: it places, never moves.
  expect(gestureOf(true, 2)).toBe('place')
  // The first point is index 0, a point all the same.
  expect(gestureOf(false, 0)).toBe('move')
  // A held press ends on a command key (undo, redo), so a drag never goes on past a history
  // change; a bare modifier, Shift, or a plain key leaves it be.
  expect(endsPress({ key: 'z', ctrlKey: false, metaKey: true })).toBe(true)
  expect(endsPress({ key: 'z', ctrlKey: true, metaKey: false })).toBe(true)
  expect(endsPress({ key: 'Meta', ctrlKey: false, metaKey: true })).toBe(false)
  expect(endsPress({ key: 'Shift', ctrlKey: false, metaKey: false })).toBe(false)
  expect(endsPress({ key: 'z', ctrlKey: false, metaKey: false })).toBe(false)
})

spec('ui:panel:the-cursor-follows-shift-and-the-pan', () => {
  expect(cursorOf(true, false)).toBe('crosshair')
  expect(cursorOf(false, false)).toBe('grab')
  expect(cursorOf(false, true)).toBe('grabbing')
  // A pan or a move under way is the grabbing hand whatever Shift says.
  expect(cursorOf(true, true)).toBe('grabbing')
})
