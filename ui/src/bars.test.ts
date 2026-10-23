import { expect } from 'vitest'
import { bar, failed } from './bars'
import { spec } from './test/spec'
import type { JobSlot } from './types'

const idle = { changes: 0, preparing: false, images: 0, rendering: false }

spec('ui:render:prepare-takes-the-bar-first', () => {
  expect(bar({ ...idle, changes: 2, images: 3 })).toBe('prepare')
  expect(bar({ ...idle, preparing: true, images: 3 })).toBe('prepare')
  expect(bar({ ...idle, images: 3 })).toBe('render')
  expect(bar({ ...idle, rendering: true })).toBe('render')
  expect(bar(idle)).toBeNull()
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
})
