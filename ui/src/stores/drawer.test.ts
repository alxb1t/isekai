import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import { afterEach, beforeEach, expect, vi } from 'vitest'
import { spec } from '../test/spec'
import type { JobSlot } from '../types'
import { useDrawerStore } from './drawer'
import { useLiveStore } from './live'

/* Each record request waits on its own answer, released in whatever order a test
   chooses; a hub request is answered at once with no source. */
let records: { url: string; answer: (value: object) => void }[]

beforeEach(() => {
  setActivePinia(createPinia())
  records = []
  vi.stubGlobal('fetch', (url: string) =>
    url.endsWith('/hub')
      ? Promise.resolve({ ok: true, json: async () => ({ collection: 'b', flows: [], sources: [] }) })
      : new Promise((resolve) =>
          records.push({ url, answer: (value) => resolve({ ok: true, json: async () => value }) }),
        ),
  )
})

afterEach(() => {
  vi.unstubAllGlobals()
})

/* The render slot holding session `id` of collection `b`, in `state`. */
const slot = (id: string, state: JobSlot['state']): JobSlot => ({
  kind: 'render',
  state,
  collection: 'b',
  flow: null,
  stage: null,
  message: null,
  session: { id, started: '', ended: null, limit: 1200, of: 1, steps: {}, images: [] },
})

spec('ui:sessions:the-selected-record-keeps-the-newest-response', async () => {
  const drawer = useDrawerStore()
  const older = drawer.show(['b'], 's')
  const newer = drawer.refresh()
  records[1].answer({ id: 's', outcome: 'done', images: [{ seed: '7' }] })
  await newer
  records[0].answer({ id: 's', outcome: 'running', images: [] })
  await older
  expect(drawer.record?.outcome).toBe('done')
  expect(drawer.record?.images).toHaveLength(1)
})

spec('ui:sessions:the-drawer-keeps-the-last-session', async () => {
  const drawer = useDrawerStore()
  const live = useLiveStore()
  live.hold(slot('s1', 'running'))
  await nextTick()
  expect(drawer.shown).toEqual({ id: 's1', collections: ['b'] })
  records.at(-1)?.answer({ id: 's1', outcome: 'running', images: [] })

  // It ends: the slot's last move reads the record once more, and it stays.
  live.hold(slot('s1', 'done'))
  await nextTick()
  expect(records.at(-1)?.url).toBe('/api/c/b/sessions/s1')
  records.at(-1)?.answer({ id: 's1', outcome: 'done', images: [{ seed: '7' }] })
  await vi.waitFor(() => expect(drawer.record?.outcome).toBe('done'))
  expect(drawer.shown).toEqual({ id: 's1', collections: ['b'] })

  live.hold(slot('s2', 'running'))
  await nextTick()
  expect(drawer.shown).toEqual({ id: 's2', collections: ['b'] })
  expect(drawer.record).toBeNull()
  records.at(-1)?.answer({ id: 's2', outcome: 'running', images: [] })
  await vi.waitFor(() => expect(drawer.record?.id).toBe('s2'))

  // A render of many collections reads each collection's record of its id.
  live.hold({ ...slot('s3', 'running'), collections: ['b', 'c'] })
  await nextTick()
  expect(drawer.shown).toEqual({ id: 's3', collections: ['b', 'c'] })
  expect(records.slice(-2).map((one) => one.url)).toEqual([
    '/api/c/b/sessions/s3',
    '/api/c/c/sessions/s3',
  ])
  for (const one of records.slice(-2)) one.answer({ id: 's3', outcome: 'running', images: [] })
  await vi.waitFor(() => expect(Object.keys(drawer.records ?? {})).toEqual(['b', 'c']))
})
