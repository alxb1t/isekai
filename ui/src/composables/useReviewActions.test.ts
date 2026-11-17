import { createPinia, setActivePinia } from 'pinia'
import { type EffectScope, effectScope } from 'vue'
import { afterEach, beforeEach, expect, vi } from 'vitest'
import { spec } from '../test/spec'
import { useLiveStore } from '../stores/live'
import type { InputDetail, JobSlot } from '../types'
import { useApproval } from './useApproval'
import { useReviewActions } from './useReviewActions'
import { useSheet } from './useSheet'

/* `fetch` is stubbed with answers the test releases by hand, so the order in
   which a save, an approval and a read answer is the test's to choose. */
interface Call {
  url: string
  init: RequestInit | undefined
  answer: (body: unknown) => void
  refuse: (message: string) => void
}

let calls: Call[] = []
let scope: EffectScope | undefined

/* A sheet of `id`; an approved one is read-only. */
function detail(id: string, saved: number, given: { approved?: boolean } = {}): InputDetail {
  const approved = given.approved ?? false
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
    wd14: null,
    tags: null,
    fields: { hair: ['long hair'] },
    renders: { count: 1, seeds: [] },
    revision: null,
    drafted: null,
    readonly: approved,
    draft: '001.draft.json',
    approved: approved ? '001.approved.json' : null,
    saved,
    approved_at: null,
    cancel: 'f is at its draft 001.draft.json, with no approval',
    budget: { total: 2, per_field: { hair: 2 }, overhead: 0, window: 75 },
  }
}

function receipt(saved: number): unknown {
  return { draft: '001.draft.json', saved, budget: detail('x', saved).budget }
}

/* A render slot in `state` over `collection`. */
function render(state: JobSlot['state'], collection: string): JobSlot {
  return { kind: 'render', collection, state, flow: null, stage: null, message: null }
}

/* Answer the oldest unanswered call to `url`, then let its awaits run. */
async function answer(url: string, body: unknown): Promise<void> {
  const at = calls.findIndex((call) => call.url === url)
  const [call] = calls.splice(at, 1)
  call.answer(body)
  await vi.advanceTimersByTimeAsync(0)
}

/* Refuse the oldest unanswered call to `url`, as the server's 409 does. */
async function refuse(url: string, message: string): Promise<void> {
  const at = calls.findIndex((call) => call.url === url)
  const [call] = calls.splice(at, 1)
  call.refuse(message)
  await vi.advanceTimersByTimeAsync(0)
}

/* The actions over the sheet of collection `b` and flow `f`, with the digest `a` open. */
function mount() {
  const made = effectScope()
  scope = made
  return made.run(() => {
    const sheet = useSheet({ collection: 'b', flow: 'f' })
    const approval = useApproval()
    const load = vi.fn(async () => undefined)
    const settled = vi.fn()
    const actions = useReviewActions({
      collection: () => 'b',
      flow: () => 'f',
      digest: () => 'a',
      sheet,
      queue: { load },
      approval,
      settled,
    })
    return { sheet, approval, load, settled, actions, live: useLiveStore() }
  })!
}

beforeEach(() => {
  vi.useFakeTimers()
  setActivePinia(createPinia())
  calls = []
  vi.stubGlobal(
    'fetch',
    (url: string, init?: RequestInit) =>
      new Promise((resolve) =>
        calls.push({
          url,
          init,
          answer: (body) => resolve({ ok: true, json: async () => body }),
          refuse: (message) => resolve({ ok: false, status: 409, json: async () => ({ refusal: message }) }),
        }),
      ),
  )
})

afterEach(() => {
  scope?.stop()
  scope = undefined
  vi.unstubAllGlobals()
  vi.useRealTimers()
})

spec('ui:save:an-approval-waits-for-a-save-in-flight', async () => {
  const { sheet, approval, load, settled, actions } = mount()
  const opened = sheet.open('a')
  await answer('/api/c/b/review/a/f', detail('a', 10))
  await opened
  sheet.commit('hair', 'brown hair', null)
  void sheet.flush()
  // A second tag inside the first save's round trip: pending when Approve is pressed.
  sheet.commit('hair', 'short hair', null)

  const approving = actions.approve()
  await vi.advanceTimersByTimeAsync(0)
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
  expect(load).not.toHaveBeenCalled()

  // The approval stays on the sheet: the collection and the sheet are read again.
  await answer('/api/c/b/review/a/f/approve', { approved: '001.approved.json', warnings: [], at: 13 })
  expect(approval.at.value).toBe(13)
  expect(load).toHaveBeenCalledTimes(1)
  expect(calls.map((call) => call.url)).toEqual(['/api/c/b/review/a/f'])
  await answer('/api/c/b/review/a/f', detail('a', 13, { approved: true }))
  await approving
  expect(settled).toHaveBeenCalledTimes(1)
  expect(sheet.readonly.value).toBe(true)
})

spec('ui:review:a-refused-save-is-shown', async () => {
  const { sheet, actions } = mount()
  const opened = sheet.open('a')
  await answer('/api/c/b/review/a/f', detail('a', 10))
  await opened

  // The only save is refused: the approval is not sent, and the sheet's message is the page's.
  sheet.commit('hair', 'brown hair', null)
  const approving = actions.approve()
  await refuse('/api/c/b/review/a/f/draft', 'a draft is not at that save')
  await approving
  expect(calls).toHaveLength(0)
  expect(actions.refusal.value).toBe('a draft is not at that save')

  // A refused save stops a discard in the same way.
  sheet.commit('hair', 'short hair', null)
  const discarding = actions.discard()
  await refuse('/api/c/b/review/a/f/draft', 'a draft is not at that save')
  await discarding
  expect(calls).toHaveLength(0)
  expect(actions.refusal.value).toBe('a draft is not at that save')
})

spec('ui:review:the-cancel-follows-the-render', async () => {
  const { sheet, load, live } = mount()
  const opened = sheet.open('a')
  await answer('/api/c/b/review/a/f', detail('a', 10, { approved: true }))
  await opened
  expect(load).not.toHaveBeenCalled()

  // An approved sheet is read again when a render of its collection starts, and when it ends.
  live.jobs = { prepare: null, render: render('running', 'b') }
  await vi.advanceTimersByTimeAsync(0)
  expect(load).toHaveBeenCalledTimes(1)
  expect(calls.map((call) => call.url)).toEqual(['/api/c/b/review/a/f'])
  await answer('/api/c/b/review/a/f', detail('a', 10, { approved: true }))

  live.jobs = { prepare: null, render: render('done', 'b') }
  await vi.advanceTimersByTimeAsync(0)
  expect(load).toHaveBeenCalledTimes(2)
  expect(calls.map((call) => call.url)).toEqual(['/api/c/b/review/a/f'])
  await answer('/api/c/b/review/a/f', detail('a', 10, { approved: true }))

  // An editable sheet is not.
  const editing = sheet.open('a')
  await answer('/api/c/b/review/a/f', detail('a', 10))
  await editing
  live.jobs = { prepare: null, render: render('running', 'b') }
  await vi.advanceTimersByTimeAsync(0)
  expect(load).toHaveBeenCalledTimes(2)
  expect(calls).toHaveLength(0)
})

spec('ui:review:a-render-that-moves-during-the-read-is-read-again', async () => {
  const { sheet, load, live } = mount()

  // The slot moves while the sheet loads: nothing is read until it lands approved.
  const opened = sheet.open('a')
  live.jobs = { prepare: null, render: render('running', 'b') }
  await vi.advanceTimersByTimeAsync(0)
  expect(load).not.toHaveBeenCalled()
  expect(calls.map((call) => call.url)).toEqual(['/api/c/b/review/a/f'])
  await answer('/api/c/b/review/a/f', detail('a', 10, { approved: true }))
  await opened
  expect(load).toHaveBeenCalledTimes(1)
  expect(calls.map((call) => call.url)).toEqual(['/api/c/b/review/a/f'])
  await answer('/api/c/b/review/a/f', detail('a', 10, { approved: true }))

  // Landing editable, it is not read again.
  const editing = sheet.open('a')
  live.jobs = { prepare: null, render: render('done', 'b') }
  await vi.advanceTimersByTimeAsync(0)
  expect(calls.map((call) => call.url)).toEqual(['/api/c/b/review/a/f'])
  await answer('/api/c/b/review/a/f', detail('a', 10))
  await editing
  expect(load).toHaveBeenCalledTimes(1)
  expect(calls).toHaveLength(0)
})
