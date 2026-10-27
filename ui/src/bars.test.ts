import { expect } from 'vitest'
import { bar, dismiss, failed, held, planOf, reasons, waiting } from './bars'
import { spec } from './test/spec'
import type { JobSlot } from './types'

const idle = {
  changes: 0,
  preparing: false,
  images: 0,
  refused: false,
  rendering: false,
  plan: null,
}

spec('ui:render:prepare-takes-the-bar-first', () => {
  expect(bar({ ...idle, changes: 2, images: 3 })).toBe('prepare')
  expect(bar({ ...idle, preparing: true, images: 3 })).toBe('prepare')
  expect(bar({ ...idle, images: 3 })).toBe('render')
  expect(bar({ ...idle, rendering: true })).toBe('render')
  expect(bar(idle)).toBeNull()
  // A count the render stage refuses keeps the bar, so its reason is on screen.
  expect(bar({ ...idle, refused: true })).toBe('render')
})

spec('ui:render:a-refused-count-is-shown', () => {
  // A refused count keeps the Render bar with no image short, so its reason is on screen.
  expect(bar({ ...idle, refused: true })).toBe('render')
  expect(bar({ ...idle, changes: 1, refused: true })).toBe('prepare')
  // A hold, such as no key, is shown beside the refusal rather than in its place.
  const noKey = 'No RunPod key: add RUNPOD_API_KEY to .env'
  const damaged = '0001.approved.json: `renders.count` is 0; restore it'
  expect(reasons(noKey, damaged)).toEqual([noKey, damaged])
  expect(reasons(damaged, damaged)).toEqual([damaged])
  expect(reasons(null, null)).toEqual([])
})

spec('ui:render:a-running-session-shows-its-totals', () => {
  const session = { id: 's', started: '', ended: null, limit: 630, of: 3, steps: {}, images: [] }
  const running = slot({ kind: 'render', state: 'running', message: null, session })
  // Three images in the session's plan and a fourth short outside it.
  const state = { ...idle, images: 4, rendering: true, plan: planOf(running) }
  expect(bar(state)).toBe('session')
  expect(waiting(state)).toBe('1 image waits for the next session')
  // A landed image is short no more, so the line holds as the offer is read again.
  const image = { digest: 'd', flow: 'f', version: 1, seed: '7' }
  const landed = planOf({ ...running, session: { ...session, images: [image] } })
  expect(waiting({ images: 3, plan: landed })).toBe('1 image waits for the next session')
  expect(waiting({ images: 2, plan: landed })).toBeNull()
  // An ended session has no plan, so the count and Render come back.
  expect(planOf({ ...running, state: 'done' })).toBeNull()
  expect(bar({ ...state, plan: null })).toBe('render')
})

function slot(over: Partial<JobSlot>): JobSlot {
  return {
    kind: 'prepare',
    collection: 'b',
    state: 'failed',
    flow: null,
    stage: null,
    message: 'refused: see log.txt',
    ...over,
  }
}

spec('ui:events:a-hub-opened-after-a-failure-shows-it', () => {
  expect(failed(slot({}), 'b')).toBe('refused: see log.txt')
  expect(failed(slot({ collection: 'other' }), 'b')).toBeNull()
  expect(failed(slot({ kind: 'render' }), 'b')).toBeNull()
  expect(failed(slot({ state: 'done' }), 'b')).toBeNull()
  expect(failed(null, 'b')).toBeNull()
  // A Discard on another collection's hub leaves this collection's failure shown.
  const first = slot({ progress: { started: '10:00', of: 2, done: 1 } })
  dismiss(first, 'other')
  expect(failed({ ...first }, 'b')).toBe('refused: see log.txt')
  // Once discarded, a hub opened again in this page leaves it dismissed; the next failure shows.
  dismiss(first, 'b')
  expect(failed({ ...first }, 'b')).toBeNull()
  expect(failed(slot({ progress: { started: '10:05', of: 2, done: 0 } }), 'b')).toBe(
    'refused: see log.txt',
  )
})

spec('ui:prepare:another-batchs-prepare-is-disabled', () => {
  const running = slot({ state: 'running', message: null })
  expect(held(running, 'other')).toBe('Prepare is running on b')
  expect(held(running, 'b')).toBeNull()
  expect(held(slot({}), 'other')).toBeNull()
  expect(held(null, 'other')).toBeNull()
})
