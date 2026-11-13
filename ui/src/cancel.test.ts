import { expect, vi } from 'vitest'
import { holdsCancel, readsAgain, rereads, type Reading } from './cancel'
import { spec } from './test/spec'
import type { JobSlot } from './types'

/* A render slot in `state`, over `collection` and any others. */
function render(state: JobSlot['state'], collection: string, collections?: string[]): JobSlot {
  return { kind: 'render', collection, collections, state, flow: null, stage: null, message: null }
}

/* An approved sheet that is not being read, unless `given` says otherwise. */
function sheet(given: Partial<Reading> = {}): Reading {
  return { loading: false, readonly: true, detail: {}, ...given }
}

spec('ui:review:the-cancel-follows-the-render', () => {
  const idle = null
  const running = render('running', 'a')
  const done = render('done', 'a')

  expect(readsAgain(idle, running, 'a', sheet())).toBe('now')
  expect(readsAgain(running, done, 'a', sheet())).toBe('now')
  expect(readsAgain(running, null, 'a', sheet())).toBe('now')
  expect(readsAgain(render('running', 'b', ['b', 'a']), done, 'a', sheet())).toBe('now')

  expect(readsAgain(idle, render('running', 'b'), 'a', sheet())).toBe('no')
  expect(readsAgain(render('running', 'b'), render('done', 'b'), 'a', sheet())).toBe('no')
  expect(readsAgain(running, running, 'a', sheet())).toBe('no')
  expect(readsAgain(done, render('failed', 'a'), 'a', sheet())).toBe('no')

  expect(readsAgain(idle, running, 'a', sheet({ readonly: false }))).toBe('no')
  expect(readsAgain(running, done, 'a', sheet({ readonly: false }))).toBe('no')

  expect(readsAgain(idle, running, 'a', sheet({ loading: true }))).toBe('later')
  expect(readsAgain(running, done, 'a', sheet({ loading: true }))).toBe('later')
  expect(readsAgain(idle, render('running', 'b'), 'a', sheet({ loading: true }))).toBe('no')
  expect(readsAgain(idle, running, 'a', sheet({ detail: null }))).toBe('no')

  expect(holdsCancel(running, 'a')).toBe(true)
  expect(holdsCancel(done, 'a')).toBe(false)
})

spec('ui:review:a-render-that-moves-during-the-read-is-read-again', () => {
  const running = render('running', 'a')
  const held = (given: Partial<Reading> = {}) => {
    const now = sheet(given)
    return {
      loading: { value: now.loading },
      readonly: { value: now.readonly },
      detail: { value: now.detail },
    }
  }

  const landing = held({ loading: true })
  const reread = vi.fn()
  const follow = rereads(() => 'a', landing, reread)
  follow.moved(null, running)
  expect(reread).not.toHaveBeenCalled()
  landing.loading.value = false
  follow.landed()
  expect(reread).toHaveBeenCalledTimes(1)
  follow.landed()
  expect(reread).toHaveBeenCalledTimes(1)

  const open = held({ loading: true })
  const never = vi.fn()
  const unapproved = rereads(() => 'a', open, never)
  unapproved.moved(null, running)
  open.loading.value = false
  open.readonly.value = false
  unapproved.landed()
  expect(never).not.toHaveBeenCalled()

  const slow = held({ loading: true })
  const later = vi.fn()
  const waiting = rereads(() => 'a', slow, later)
  waiting.moved(null, running)
  waiting.landed()
  expect(later).not.toHaveBeenCalled()
  slow.loading.value = false
  waiting.landed()
  expect(later).toHaveBeenCalledTimes(1)

  const quiet = held()
  const at = vi.fn()
  rereads(() => 'a', quiet, at).moved(null, running)
  expect(at).toHaveBeenCalledTimes(1)
})
