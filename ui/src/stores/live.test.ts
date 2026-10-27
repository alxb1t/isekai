import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, expect, vi } from 'vitest'
import { spec } from '../test/spec'
import { billingState, useLiveStore } from './live'

/* A stream that records where it was opened and whether it was closed, and
   sends what a test hands it to the store's listeners. */
class FakeSource {
  static opened: FakeSource[] = []
  closed = false
  listeners = new Map<string, (event: { data: string }) => void>()
  constructor(readonly url: string) {
    FakeSource.opened.push(this)
  }
  addEventListener(kind: string, listener: (event: { data: string }) => void): void {
    this.listeners.set(kind, listener)
  }
  close(): void {
    this.closed = true
  }
  send(kind: string, data: unknown): void {
    this.listeners.get(kind)?.({ data: JSON.stringify(data) })
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

  live.follow({ collection: 'a' })
  live.follow({ collection: 'a' })
  live.follow({ staging: 's1' })

  expect(FakeSource.opened.map((one) => one.url)).toEqual([
    '/events?collection=a',
    '/events?collection=a&staging=s1',
  ])
  expect(FakeSource.opened.map((one) => one.closed)).toEqual([true, false])
})

spec('ui:events:a-job-event-fills-its-kinds-slot', () => {
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => ({ sessions: [] }) })))
  const live = useLiveStore()
  live.follow({ collection: 'b' })
  const [stream] = FakeSource.opened
  const slot = { collection: 'b', state: 'running', flow: null, stage: null, message: null }
  const prepare = { ...slot, kind: 'prepare' }
  const session = { id: 's', started: '', ended: null, limit: 1, of: 1, steps: {}, images: [] }
  const render = { ...slot, kind: 'render', session }

  stream.send('snapshot', { jobs: { prepare, render: null }, billing: { pod: false, volume: null } })
  stream.send('job', render)

  expect(live.jobs).toEqual({ prepare, render })
})

spec('ui:sessions:a-terminal-render-stays-live', async () => {
  const terminal = { collection: 'b', id: '20261024T091200Z', started: '2026-10-24T09:12:00Z' }
  let records = [terminal]
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => ({ sessions: records }) })))
  const live = useLiveStore()
  live.follow({ collection: null })
  await vi.advanceTimersByTimeAsync(0)
  expect(live.jobs).toEqual({ prepare: null, render: null })
  expect(live.renderRunning).toBe(true)
  expect(live.activeRender).toEqual({
    collections: ['b'],
    id: terminal.id,
    started: terminal.started,
  })
  // One render's records in two collections are one render.
  records = [terminal, { ...terminal, collection: 'c' }]
  await vi.advanceTimersByTimeAsync(2000)
  expect(live.activeRender?.collections).toEqual(['b', 'c'])
  records = [terminal]
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
