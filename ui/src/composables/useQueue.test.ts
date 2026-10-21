import { afterEach, beforeEach, expect, vi } from 'vitest'
import { spec } from '../test/spec'
import type { HubInfo, InputStatus } from '../types'
import { useQueue } from './useQueue'

/* `fetch` answers the hub with a batch built here, so the run directories the
   count must agree with are the ones this file declares. */
let hub: HubInfo

function source(name: string, status: InputStatus) {
  return {
    name,
    digest: name,
    width: 1,
    height: 1,
    cells: { f: { stage: null, renders: 0, refusal: null, status } },
  }
}

beforeEach(() => {
  vi.stubGlobal('fetch', async () => ({ ok: true, json: async () => hub }))
})

afterEach(() => {
  vi.unstubAllGlobals()
})


spec('ui:approval:a-re-opened-input-is-not-counted-approved', async () => {
  // Two runs hold an approved artifact in `f`: `a` approved, `b` re-opened
  // over its approved one. `c` holds a draft alone.
  hub = {
    batch: 'b',
    flows: ['f'],
    sources: [source('a', 'approved'), source('b', 're-opened'), source('c', 'draft')],
  }
  const held = 2
  const queue = useQueue('b', 'f', () => 'c')

  await queue.load()

  const reopened = queue.inputs.value.find((input) => input.id === 'b')
  expect(reopened?.status).toBe('re-opened')
  expect(queue.approved.value).toBe(held)
})
