import { afterEach, beforeEach, expect, vi } from 'vitest'
import { spec } from '../test/spec'
import type { InputDetail } from '../types'
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
    width: 1,
    height: 1,
    caption: null,
    caption_command: null,
    wd14: null,
    tags: null,
    fields: { hair: ['long hair'] },
    readonly: false,
    draft: '001.draft.json',
    approved: null,
    saved,
    approved_at: null,
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
  const sheet = useSheet()
  const opened = sheet.open('a')
  await answer('/api/inputs/a', detail('a', 10))
  await opened
  sheet.commit('hair', 'brown hair', null)
  void sheet.flush()
  expect(sheet.saving.value).toBe(true)

  const switched = sheet.open('b')
  await answer('/api/inputs/b', detail('b', 20))
  await switched
  expect(sheet.saving.value).toBe(true)

  await answer('/api/inputs/a/draft', receipt(11))
  expect(sheet.saving.value).toBe(false)
  expect(sheet.saved.value).toBe(20)

  sheet.commit('hair', 'short hair', null)
  void sheet.flush()
  expect(sheet.saving.value).toBe(true)
  await answer('/api/inputs/b/draft', receipt(21))
  expect(sheet.saving.value).toBe(false)
  expect(sheet.saved.value).toBe(21)
})

spec('ui:save:a-pending-edit-is-sent-on-leaving', async () => {
  const sheet = useSheet()
  const opened = sheet.open('a')
  await answer('/api/inputs/a', detail('a', 10))
  await opened
  sheet.commit('hair', 'brown hair', null)
  expect(calls).toHaveLength(0)

  void sheet.flush()
  expect(calls).toHaveLength(1)
  const [put] = calls
  expect(put.url).toBe('/api/inputs/a/draft')
  expect(put.init?.method).toBe('PUT')
  expect(put.init?.keepalive).toBe(true)
  expect(JSON.parse(String(put.init?.body)).fields.hair).toEqual(['long hair', 'brown hair'])
})
