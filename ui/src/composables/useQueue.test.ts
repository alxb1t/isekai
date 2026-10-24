import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, expect, vi } from 'vitest'
import { spec } from '../test/spec'
import type { HubInfo, InputStatus } from '../types'
import { head, rail, useQueue, waiting } from './useQueue'

/* `fetch` answers the hub with a batch built here, so the run directories the
   count must agree with are the ones this file declares. The rail reads it
   through the batch store, fresh for each test. */
let hub: HubInfo

function source(name: string, status: InputStatus, short: number | null = null) {
  return {
    name,
    digest: name,
    width: 1,
    height: 1,
    cells: {
      f: { stage: null, renders: 0, refusal: null, status, newest: null, short, images: [] },
    },
    carries: [],
  }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.stubGlobal('fetch', async () => ({ ok: true, json: async () => hub }))
})

afterEach(() => {
  vi.unstubAllGlobals()
})

spec('ui:approval:a-re-opened-input-is-not-counted-approved', async () => {
  // Two of the rail's runs hold an approved artifact in `f`: `a` approved and
  // short, `b` re-opened over its approved one. `c` holds a draft alone, and `d`
  // is approved with all its images, so the rail leaves it out.
  hub = {
    batch: 'b',
    flows: ['f'],
    sources: [
      source('a', 'approved', 1),
      source('b', 're-opened'),
      source('c', 'draft'),
      source('d', 'approved', 0),
    ],
  }
  const held = 2
  const queue = useQueue('b', 'f', () => 'c')

  await queue.load()

  const reopened = queue.inputs.value.find((input) => input.id === 'b')
  expect(reopened?.status).toBe('re-opened')
  expect(queue.inputs.value.map((input) => input.id)).toEqual(['a', 'b', 'c'])
  expect(queue.approved.value).toBe(held)
})

spec('ui:review:the-rail-holds-every-unrendered-sheet', () => {
  // `a` waits for review, `b` is approved and lacks an image, `c` has all its images.
  const info: HubInfo = {
    batch: 'b',
    flows: ['f'],
    sources: [source('a', 'draft'), source('b', 'approved', 1), source('c', 'approved', 0)],
  }

  const listed = rail(info, 'f', 'a')

  expect(listed.map((input) => [input.id, input.status])).toEqual([
    ['a', 'draft'],
    ['b', 'approved'],
  ])
  // The open sheet stays, though it has all its images.
  expect(rail(info, 'f', 'c').map((input) => input.id)).toEqual(['a', 'b', 'c'])
})

spec('ui:review:a-batch-opens-its-head', () => {
  // `a` is approved and lacks an image; `b` waits for review; `c` has all its images.
  const batch = (b: InputStatus): HubInfo => ({
    batch: 'b',
    flows: ['f'],
    sources: [source('a', 'approved', 1), source('b', b), source('c', 'approved', 0)],
  })

  expect(head(batch('draft'))).toEqual({ digest: 'b', flow: 'f' })
  expect(head(batch('approved'))).toEqual({ digest: 'a', flow: 'f' })
  const done = batch('approved')
  done.sources[0].cells.f.short = 0
  expect(head(done)).toBeNull()
})

spec('ui:review:the-rail-names-the-other-flows-waiting', () => {
  // `g` holds one unapproved sheet and `h` none; `f` is the flow open.
  const one = source('a', 'draft')
  const info: HubInfo = {
    batch: 'b',
    flows: ['f', 'g', 'h'],
    sources: [
      {
        ...one,
        cells: { ...one.cells, g: { ...one.cells.f }, h: { ...one.cells.f, status: 'approved' } },
      },
    ],
  }

  expect(waiting(info, 'f')).toEqual([{ flow: 'g', count: 1 }])
  // From the flow after the open one, round to the one before it.
  expect(waiting(info, 'h')).toEqual([
    { flow: 'f', count: 1 },
    { flow: 'g', count: 1 },
  ])
})
