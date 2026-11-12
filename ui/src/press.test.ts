import { expect } from 'vitest'
import { held, moved, redone, undone } from './pairs'
import { type Rules, drafted, moved as movedVertex, redone as redoneDraft, undone as undoneDraft } from './polygon'
import { cursorOf, endsPress, gestureOf, pressing } from './press'
import { spec } from './test/spec'
import type { Point } from './types'

const RULES: Rules = { min: 3, max: 5, width: 300, height: 300 }

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

  // The press itself: a drag runs fresh once, a pan runs by the pointer's travel, and a press
  // within the slop is a click on release.
  const hold = pressing(4)
  hold.down([0, 0], false, 1)
  expect(hold.move([2, 2])).toEqual({ kind: 'still' })
  expect(hold.move([10, 0])).toEqual({ kind: 'drag', index: 1, fresh: true })
  expect(hold.move([12, 0])).toEqual({ kind: 'drag', index: 1, fresh: false })
  expect(hold.up()).toEqual({ click: false, shift: false })
  expect(hold.move([12, 0])).toEqual({ kind: 'hover' })
  hold.down([0, 0], false, null)
  expect(hold.move([10, 3])).toEqual({ kind: 'pan', dx: 10, dy: 3 })
  expect(hold.move([11, 3])).toEqual({ kind: 'pan', dx: 1, dy: 0 })
  hold.cancel()
  hold.down([0, 0], true, null)
  expect(hold.up()).toEqual({ click: true, shift: true })
  expect(hold.up()).toBeNull()

  // A drag broken by undo goes on writing nothing: drag the point, press undo with the button
  // down, move on and release, and the saved point is the one before the drag, redo bringing
  // the drag back. The pairs and the outline are one gesture lifecycle, each with its own history.
  const undo = { key: 'z', ctrlKey: false, metaKey: true }
  const pairs = held([[[10, 10], [200, 200]]])
  const outline = drafted([[10, 10], [90, 10], [90, 90]], false)
  const states = { pairs, outline }
  const edits = {
    drag: (index: number, at: Point, fresh: boolean): void => {
      states.pairs = moved(states.pairs, index, 'a', at, fresh)
      states.outline = movedVertex(states.outline, index, at, RULES, fresh)
    },
    undo: (): void => {
      states.pairs = undone(states.pairs)
      states.outline = undoneDraft(states.outline)
    },
  }
  const interrupted = pressing(4)
  interrupted.down([10, 10], false, 0)
  for (const at of [[40, 40], [42, 42]] as Point[]) {
    const step = interrupted.move(at)
    if (step.kind === 'drag') edits.drag(step.index, at, step.fresh)
  }
  expect(states.pairs.slots[0].a).toEqual([42, 42])
  edits.undo()
  interrupted.key(undo)
  for (const at of [[50, 50], [60, 60]] as Point[]) {
    const step = interrupted.move(at)
    if (step.kind === 'drag') edits.drag(step.index, at, step.fresh)
  }
  expect(interrupted.up()).toBeNull()
  expect(states.pairs.slots[0].a).toEqual([10, 10])
  expect(states.pairs.past).toHaveLength(0)
  expect(redone(states.pairs).slots[0].a).toEqual([42, 42])
  expect(states.outline.points[0]).toEqual([10, 10])
  expect(states.outline.past).toHaveLength(0)
  expect(redoneDraft(states.outline).points[0]).toEqual([42, 42])
})

spec('ui:panel:the-cursor-follows-shift-and-the-pan', () => {
  expect(cursorOf(true, false)).toBe('crosshair')
  expect(cursorOf(false, false)).toBe('grab')
  expect(cursorOf(false, true)).toBe('grabbing')
  // A pan or a move under way is the grabbing hand whatever Shift says.
  expect(cursorOf(true, true)).toBe('grabbing')
})
