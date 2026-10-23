import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, expect, vi } from 'vitest'
import { spec } from '../test/spec'
import { useLiveStore } from './live'

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
