import { expect } from 'vitest'
import { holdsCancel, readsAgain } from './cancel'
import { spec } from './test/spec'
import type { JobSlot } from './types'

/* A render slot in `state`, over `collection` and any others. */
function render(state: JobSlot['state'], collection: string, collections?: string[]): JobSlot {
  return { kind: 'render', collection, collections, state, flow: null, stage: null, message: null }
}

spec('ui:review:the-cancel-follows-the-render', () => {
  const idle = null
  const running = render('running', 'a')
  const done = render('done', 'a')

  expect(readsAgain(idle, running, 'a', true)).toBe(true)
  expect(readsAgain(running, done, 'a', true)).toBe(true)
  expect(readsAgain(running, null, 'a', true)).toBe(true)
  expect(readsAgain(render('running', 'b', ['b', 'a']), done, 'a', true)).toBe(true)

  expect(readsAgain(idle, render('running', 'b'), 'a', true)).toBe(false)
  expect(readsAgain(render('running', 'b'), render('done', 'b'), 'a', true)).toBe(false)
  expect(readsAgain(running, running, 'a', true)).toBe(false)
  expect(readsAgain(done, render('failed', 'a'), 'a', true)).toBe(false)

  expect(readsAgain(idle, running, 'a', false)).toBe(false)
  expect(readsAgain(running, done, 'a', false)).toBe(false)

  expect(holdsCancel(running, 'a')).toBe(true)
  expect(holdsCancel(done, 'a')).toBe(false)
})
