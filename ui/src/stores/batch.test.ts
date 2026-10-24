import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import { afterEach, beforeEach, expect, vi } from 'vitest'
import { spec } from '../test/spec'
import type { RenderOffer } from '../types'
import { kept, useBatchStore } from './batch'
import { useLiveStore } from './live'

/* Each offer request waits on its own answer, released in whatever order a test chooses. */
let answers: ((offer: RenderOffer) => void)[]

beforeEach(() => {
  setActivePinia(createPinia())
  answers = []
  vi.stubGlobal(
    'fetch',
    () =>
      new Promise((resolve) =>
        answers.push((offer) => resolve({ ok: true, json: async () => offer })),
      ),
  )
})

afterEach(() => {
  vi.unstubAllGlobals()
})

spec('ui:render:a-stale-offer-is-dropped', async () => {
  const store = useBatchStore()
  store.open('b')
  const older = store.check()
  const newer = store.check()

  answers[1]({ disabled: null, images: 2, refused: null })
  await newer
  answers[0]({ disabled: null, images: 5, refused: null })
  await older

  expect(store.offer.images).toBe(2)
})

spec('ui:sessions:the-selected-record-keeps-the-newest-response', async () => {
  const pending: ((value: object) => void)[] = []
  vi.stubGlobal('fetch', () => new Promise((resolve) =>
    pending.push((value) => resolve({ ok: true, json: async () => value })),
  ))
  const store = useBatchStore()
  store.open('b')
  const older = store.showSession('s')
  const newer = store.showSession('s')
  pending[1]({ id: 's', outcome: 'done', images: [{ seed: '7' }] })
  await newer
  pending[0]({ id: 's', outcome: 'running', images: [] })
  await older
  expect(store.session?.outcome).toBe('done')
  expect(store.session?.images).toHaveLength(1)
})

spec('ui:sessions:an-observed-list-follows-its-render', async () => {
  const requests: { url: string; answer: (value: object) => void }[] = []
  vi.stubGlobal('fetch', (url: string) => new Promise((resolve) => requests.push({
    url,
    answer: (value) => resolve({ ok: true, json: async () => value }),
  })))
  const store = useBatchStore()
  const live = useLiveStore()
  store.open('b')
  const initial = store.reloadSessions()
  requests[0].answer({ sessions: [] })
  await initial
  const slot = (images: number, volume = 'running') => ({
    kind: 'render' as const,
    state: 'running' as const,
    batch: 'b',
    session: {
      id: 's', started: '', ended: null, limit: 1200, of: 1,
      steps: { 'volume up': volume },
      images: Array.from({ length: images }, () => ({
        digest: 'd', flow: 'f', version: 1, seed: '7',
      })),
    },
    message: null, flow: null, stage: null,
  })
  live.hold(slot(0))
  await nextTick()
  let lists = requests.filter((one) => one.url.endsWith('/sessions'))
  expect(lists).toHaveLength(2)
  // Image and volume changes during one read coalesce into one following read.
  live.hold(slot(1, 'done'))
  await nextTick()
  live.hold({
    ...slot(1, 'done'),
    session: { ...slot(1, 'done').session, steps: { pod: 'ready' } },
  })
  await nextTick()
  expect(requests.filter((one) => one.url.endsWith('/sessions'))).toHaveLength(2)
  lists[1].answer({ sessions: [{ id: 's', outcome: 'running', images: [] }] })
  await vi.waitFor(() =>
    expect(requests.filter((one) => one.url.endsWith('/sessions'))).toHaveLength(3),
  )
  lists = requests.filter((one) => one.url.endsWith('/sessions'))
  lists[2].answer({ sessions: [{ id: 's', outcome: 'running', images: [{ seed: '7' }] }] })
  await vi.waitFor(() => expect(store.sessions?.[0]?.images).toHaveLength(1))
})

spec('ui:renders:a-grid-keeps-its-focus', () => {
  const store = useBatchStore()
  const name = (one: string) => one
  store.open('b')
  expect(kept(['a', 'b', 'c'], name, store.focus.renders)).toBe('a')
  store.focus.renders = 'b'
  store.open('b')
  expect(kept(['a', 'b', 'c'], name, store.focus.renders)).toBe('b')
  // A spot gone since is the first; another batch starts from the first.
  expect(kept(['a', 'c'], name, store.focus.renders)).toBe('a')
  store.open('c')
  expect(store.focus).toEqual({ hub: null, renders: null })
})
