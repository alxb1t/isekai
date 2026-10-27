import { afterEach, beforeEach, expect, vi } from 'vitest'
import { spec } from '../test/spec'
import type { InputDetail } from '../types'
import { useApproval } from './useApproval'
import { useSheet } from './useSheet'

/* `fetch` is stubbed with answers the test releases by hand, so the order in
   which a save and an input switch answer is the test's to choose. */
interface Call {
  url: string
  init: RequestInit | undefined
  answer: (body: unknown) => void
}

let calls: Call[] = []

function detail(id: string, saved: number): InputDetail {
  return {
    id,
    run: `${id}_run`,
    flow: 'f',
    schema: ['hair'],
    vocabulary: 1,
    width: 1,
    height: 1,
    caption: null,
    caption_command: null,
    caption_from: null,
    wd14: null,
    tags: null,
    fields: { hair: ['long hair'] },
    renders: { count: 1, seeds: [] },
    revision: null,
    drafted: null,
    readonly: false,
    draft: '001.draft.json',
    approved: null,
    saved,
    approved_at: null,
    cancel: 'f has no approval to cancel',
    budget: { total: 2, per_field: { hair: 2 }, overhead: 0, window: 75 },
  }
}

function receipt(saved: number): unknown {
  return { draft: '001.draft.json', saved, budget: detail('x', saved).budget }
}

/* Answer the oldest unanswered call to `url`, then let its awaits run. */
async function answer(url: string, body: unknown): Promise<void> {
  const at = calls.findIndex((call) => call.url === url)
  const [call] = calls.splice(at, 1)
  call.answer(body)
  await vi.runAllTimersAsync()
}

beforeEach(() => {
  vi.useFakeTimers()
  calls = []
  vi.stubGlobal(
    'fetch',
    (url: string, init?: RequestInit) =>
      new Promise((resolve) =>
        calls.push({
          url,
          init,
          answer: (body) => resolve({ ok: true, json: async () => body }),
        }),
      ),
  )
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.useRealTimers()
})

spec('ui:save:a-stale-save-cannot-clear-saving', async () => {
  const sheet = useSheet({ collection: 'b', flow: 'f' })
  const opened = sheet.open('a')
  await answer('/api/c/b/review/a/f', detail('a', 10))
  await opened
  sheet.commit('hair', 'brown hair', null)
  void sheet.flush()
  expect(sheet.saving.value).toBe(true)

  const switched = sheet.open('b')
  await answer('/api/c/b/review/b/f', detail('b', 20))
  await switched
  expect(sheet.saving.value).toBe(true)

  await answer('/api/c/b/review/a/f/draft', receipt(11))
  expect(sheet.saving.value).toBe(false)
  expect(sheet.saved.value).toBe(20)

  sheet.commit('hair', 'short hair', null)
  void sheet.flush()
  expect(sheet.saving.value).toBe(true)
  await answer('/api/c/b/review/b/f/draft', receipt(21))
  expect(sheet.saving.value).toBe(false)
  expect(sheet.saved.value).toBe(21)
})

spec('ui:save:a-pending-edit-is-sent-on-leaving', async () => {
  const sheet = useSheet({ collection: 'b', flow: 'f' })
  const opened = sheet.open('a')
  await answer('/api/c/b/review/a/f', detail('a', 10))
  await opened
  sheet.commit('hair', 'brown hair', null)
  expect(calls).toHaveLength(0)

  void sheet.flush()
  expect(calls).toHaveLength(1)
  const [put] = calls
  expect(put.url).toBe('/api/c/b/review/a/f/draft')
  expect(put.init?.method).toBe('PUT')
  expect(put.init?.keepalive).toBe(true)
  expect(JSON.parse(String(put.init?.body)).fields.hair).toEqual(['long hair', 'brown hair'])

  // Review's switch inside that save's round trip: the edit is sent once it answers, stating the draft it wrote.
  sheet.commit('hair', 'short hair', null)
  void sheet.flush()
  const switched = sheet.open('b')
  expect(calls.map((call) => call.url)).toEqual(['/api/c/b/review/a/f/draft', '/api/c/b/review/b/f'])
  await answer('/api/c/b/review/a/f/draft', receipt(11))
  const left = calls.find((call) => call.url === '/api/c/b/review/a/f/draft')
  expect(left?.init?.keepalive).toBe(true)
  expect(JSON.parse(String(left?.init?.body)).saved).toBe(11)
  expect(JSON.parse(String(left?.init?.body)).fields.hair).toEqual(['long hair', 'brown hair', 'short hair'])
  await answer('/api/c/b/review/b/f', detail('b', 20))
  await switched
  await answer('/api/c/b/review/a/f/draft', receipt(12))
  expect(sheet.saved.value).toBe(20)

  // Closing inside a save's round trip: no edit can state its receipt before the page goes, so the page asks.
  sheet.commit('hair', 'brown hair', null)
  void sheet.flush()
  sheet.commit('hair', 'short hair', null)
  expect(sheet.leave()).toBe(true)
  expect(calls.map((call) => call.url)).toEqual(['/api/c/b/review/b/f/draft'])
  // Staying, the edit is sent once that save answers, stating the draft it wrote.
  await answer('/api/c/b/review/b/f/draft', receipt(21))
  const [kept] = calls
  expect(kept.init?.keepalive).toBe(true)
  expect(JSON.parse(String(kept.init?.body)).saved).toBe(21)
  expect(JSON.parse(String(kept.init?.body)).fields.hair).toEqual(['long hair', 'brown hair', 'short hair'])
  await answer('/api/c/b/review/b/f/draft', receipt(22))
  expect(sheet.leave()).toBe(false)
})

spec('ui:save:an-approval-waits-for-a-save-in-flight', async () => {
  const sheet = useSheet({ collection: 'b', flow: 'f' })
  const approval = useApproval()
  const opened = sheet.open('a')
  await answer('/api/c/b/review/a/f', detail('a', 10))
  await opened
  sheet.commit('hair', 'brown hair', null)
  void sheet.flush()
  // A second tag inside the first save's round trip: pending when Approve is pressed.
  sheet.commit('hair', 'short hair', null)

  // Review's Approve: the draft on disk first, then the approval stating it.
  const approving = (async () => {
    if (await sheet.flush()) await approval.approve({ collection: 'b', digest: 'a', flow: 'f' }, sheet.saved.value)
  })()
  await vi.runAllTimersAsync()
  expect(calls.map((call) => call.url)).toEqual(['/api/c/b/review/a/f/draft'])

  // The pending edit is sent once the first save answers, stating the draft it wrote.
  await answer('/api/c/b/review/a/f/draft', receipt(11))
  const [second] = calls
  expect(second.url).toBe('/api/c/b/review/a/f/draft')
  const sent = JSON.parse(String(second.init?.body))
  expect(sent.saved).toBe(11)
  expect(sent.fields.hair).toEqual(['long hair', 'brown hair', 'short hair'])

  await answer('/api/c/b/review/a/f/draft', receipt(12))
  const [post] = calls
  expect(post.url).toBe('/api/c/b/review/a/f/approve')
  expect(JSON.parse(String(post.init?.body))).toEqual({ saved: 12 })
  await answer('/api/c/b/review/a/f/approve', { approved: '001.approved.json', warnings: [], at: 13 })
  await approving
  expect(approval.at.value).toBe(13)
})
