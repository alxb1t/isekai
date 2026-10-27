import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, expect, vi } from 'vitest'
import { EMPTY_CELL } from '../cells'
import { spec } from '../test/spec'
import type { HubInfo, InputStatus } from '../types'
import { flowsWaiting, head, rail, useQueue, waiting } from './useQueue'

/* `fetch` answers the hub with a collection built here, so the run directories the
   count must agree with are the ones this file declares. The rail reads it
   through the collection store, fresh for each test. */
let hub: HubInfo

function source(name: string, status: InputStatus, short: number | null = null) {
  return {
    name,
    digest: name,
    width: 1,
    height: 1,
    cells: { f: { ...EMPTY_CELL, status, short } },
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
    collection: 'b',
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
    collection: 'b',
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
  const collection = (b: InputStatus): HubInfo => ({
    collection: 'b',
    flows: ['f'],
    sources: [source('a', 'approved', 1), source('b', b), source('c', 'approved', 0)],
  })

  // One flow waits, so Review opens its head rather than the chooser.
  expect(flowsWaiting(collection('draft')).map((one) => one.flow)).toEqual(['f'])
  expect(head(collection('draft'))).toEqual({ digest: 'b', flow: 'f' })
  expect(head(collection('approved'))).toEqual({ digest: 'a', flow: 'f' })
  const done = collection('approved')
  done.sources[0].cells.f.short = 0
  expect(head(done)).toBeNull()
  expect(flowsWaiting(done)).toEqual([])
})

spec('ui:review:two-flows-waiting-open-the-chooser', () => {
  // `a` waits in `f` and `g`; `b` waits in `g` alone, approved and short; `c` waits nowhere.
  const cells = (f: InputStatus, g: InputStatus, short: number | null = null) => ({
    f: { ...EMPTY_CELL, status: f },
    g: { ...EMPTY_CELL, status: g, short },
  })
  const info: HubInfo = {
    collection: 'b',
    flows: ['f', 'g'],
    sources: [
      { ...source('a', 'draft'), cells: cells('draft', 'draft') },
      { ...source('b', 'approved', 0), cells: cells('approved', 'approved', 2) },
      { ...source('c', 'approved', 0), cells: cells('approved', 'approved', 0) },
    ],
  }

  expect(flowsWaiting(info)).toEqual([
    { flow: 'f', approve: 1, short: 0, sources: [{ name: 'a', digest: 'a' }] },
    {
      flow: 'g',
      approve: 1,
      short: 1,
      sources: [
        { name: 'a', digest: 'a' },
        { name: 'b', digest: 'b' },
      ],
    },
  ])
  // A row's ↵ opens that flow's head.
  expect(head(info, ['g'])).toEqual({ digest: 'a', flow: 'g' })
})

spec('ui:review:the-rail-names-the-other-flows-waiting', () => {
  // `g` holds one unapproved sheet and `h` none; `f` is the flow open.
  const one = source('a', 'draft')
  const info: HubInfo = {
    collection: 'b',
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
