import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, expect, vi } from 'vitest'
import { spec } from '../test/spec'
import { billingState, useLiveStore } from './live'

/* A stream that only records where it was opened and whether it was closed. */
class FakeSource {
  static opened: FakeSource[] = []
  closed = false
  constructor(readonly url: string) {
    FakeSource.opened.push(this)
  }
  addEventListener(): void {}
  close(): void {
    this.closed = true
  }
}

beforeEach(() => {
  setActivePinia(createPinia())
  FakeSource.opened = []
  vi.stubGlobal('EventSource', FakeSource)
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

spec('ui:events:one-stream-follows-the-batch-and-the-import', () => {
  const live = useLiveStore()

  live.follow({ batch: 'a' })
  live.follow({ batch: 'a' })
  live.follow({ staging: 's1' })

  expect(FakeSource.opened.map((one) => one.url)).toEqual([
    '/events?batch=a',
    '/events?batch=a&staging=s1',
  ])
  expect(FakeSource.opened.map((one) => one.closed)).toEqual([true, false])
})

spec('ui:sessions:a-terminal-render-stays-live', async () => {
  const terminal = { batch: 'b', id: '20261024T091200Z', started: '2026-10-24T09:12:00Z' }
  let records = [terminal]
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => ({ sessions: records }) })))
  const live = useLiveStore()
  live.follow({ batch: null })
  await vi.advanceTimersByTimeAsync(0)
  expect(live.job).toBeNull()
  expect(live.renderRunning).toBe(true)
  expect(live.activeRender).toMatchObject(terminal)
  // A failing read says so, and its last answer never masks a billing alert.
  const answer = { ok: false, status: 409, json: async () => ({ refusal: 'x.json: damaged' }) }
  vi.stubGlobal('fetch', vi.fn(async () => answer))
  await vi.advanceTimersByTimeAsync(2000)
  expect(live.sessionsRefusal).toBe('x.json: damaged')
  const pod = { pod: true, volume: null }
  expect(billingState(pod, live.renderRunning, live.renderConfirmed)).toBe('alert')
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => ({ sessions: records }) })))
  records = []
  await vi.advanceTimersByTimeAsync(2000)
  expect(live.sessionsRefusal).toBeNull()
  expect(live.renderRunning).toBe(false)
  expect(live.activeRender).toBeNull()
})
