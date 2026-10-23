import { expect } from 'vitest'
import { bar, dismiss, failed } from './bars'
import { spec } from './test/spec'
import type { JobSlot } from './types'

const idle = { changes: 0, preparing: false, images: 0, refused: false, rendering: false }

spec('ui:render:prepare-takes-the-bar-first', () => {
  expect(bar({ ...idle, changes: 2, images: 3 })).toBe('prepare')
  expect(bar({ ...idle, preparing: true, images: 3 })).toBe('prepare')
  expect(bar({ ...idle, images: 3 })).toBe('render')
  expect(bar({ ...idle, rendering: true })).toBe('render')
  expect(bar(idle)).toBeNull()
  // A count the render stage refuses keeps the bar, so its reason is on screen.
  expect(bar({ ...idle, refused: true })).toBe('render')
})

function slot(over: Partial<JobSlot>): JobSlot {
  return {
    kind: 'prepare',
    batch: 'b',
    state: 'failed',
    flow: null,
    stage: null,
    message: 'refused: see log.txt',
    ...over,
  }
}

spec('ui:events:a-hub-opened-after-a-failure-shows-it', () => {
  expect(failed(slot({}), 'b')).toBe('refused: see log.txt')
  expect(failed(slot({ batch: 'other' }), 'b')).toBeNull()
  expect(failed(slot({ kind: 'render' }), 'b')).toBeNull()
  expect(failed(slot({ state: 'done' }), 'b')).toBeNull()
  expect(failed(null, 'b')).toBeNull()
  // Once discarded, a hub opened again leaves it dismissed; the next failure shows.
  const first = slot({ progress: { started: '10:00', of: 2, done: 1 } })
  dismiss(first)
  expect(failed({ ...first }, 'b')).toBeNull()
  expect(failed(slot({ progress: { started: '10:05', of: 2, done: 0 } }), 'b')).toBe(
    'refused: see log.txt',
  )
})
