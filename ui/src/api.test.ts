import { afterEach, expect, vi } from 'vitest'
import {
  bakeTattoo,
  draft,
  inkView,
  keepTattoo,
  placementPreview,
  proposePairs,
  saveOutline,
  saveStageOne,
} from './api'
import type { Place, PreviewAsk } from './api'
import { spec } from './test/spec'
import wire from './test/wire.json'
import type { Outline, Pair } from './types'

const place: Place = { collection: 'b', digest: 'abc123def456', flow: 'summon-anime-wai' }

const outline: Outline = {
  points: [[10, 20], [300, 40], [200, 400]],
  closed: true,
  white: 1,
  neutral: false,
  depth: 1,
}

const pairs: Pair[] = [[[10, 20], [12, 22]]]

const ask: PreviewAsk = {
  target: 'render',
  place,
  version: 'v1',
  seed: '7',
  edit: null,
  pairs,
  limb: null,
  exclusions: [],
}

/** Stub `fetch` to answer `status` with `body` and `headers`, as a server would. */
function answered(status: number, body: string, headers: Record<string, string> = {}): void {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(body, { status, headers })))
}

interface Sent {
  url: string
  method: string | undefined
  keys: string[]
}

/** Run `call` against a `fetch` that answers 200, and return what it sent. */
async function sent(call: () => Promise<unknown>): Promise<Sent> {
  const fetcher = vi.fn(
    async () =>
      new Response('{}', {
        status: 200,
        headers: { 'X-Ink-Box': '1,2,3,4', 'X-Preview-Box': '1,2,3,4', 'X-Ink-White': '128' },
      }),
  )
  vi.stubGlobal('fetch', fetcher)
  await call()
  const [url, init] = fetcher.mock.calls[0] as unknown as [string, RequestInit]
  return { url, method: init.method, keys: Object.keys(JSON.parse(init.body as string)) }
}

/** Assert `got` is the request the fixture's entry for `builder` names. */
function holds(builder: string, got: Sent): void {
  const want = wire.bodies.find((body) => body.builder === builder)
  if (!want) throw new Error(`no entry for ${builder} in wire.json`)
  const route = new RegExp(`^${want.path.replace(/\{[^}]+\}/g, '[^/]+')}$`)
  expect(got.method).toBe(want.method)
  expect(got.url.split('?')[0]).toMatch(route)
  expect([...got.keys].sort()).toEqual([...want.keys].sort())
}

afterEach(() => {
  vi.unstubAllGlobals()
})

spec('ui:pairs:the-pairs-stay-across-steps', async () => {
  holds('saveStageOne', await sent(() => saveStageOne(place.digest, 'bow', { pairs, not_on_photo: false })))
})

spec('ui:outline-edit:a-click-adds-a-vertex-and-the-first-closes', async () => {
  holds('saveOutline', await sent(() => saveOutline(place.digest, 'bow', outline)))
})

spec('ui:outline-step:the-size-of-the-cuts-ink-is-the-outlines-box', async () => {
  holds('inkView', await sent(() => inkView('b', 'bow', outline, place)))
})

spec('ui:preview:one-ask-follows-a-burst-of-changes', async () => {
  holds('placementPreview', await sent(() => placementPreview('b', 'bow', ask)))
})

spec('ui:proposal:the-points-sent-are-the-tattoos-on-the-photograph', async () => {
  holds('proposePairs', await sent(() => proposePairs(place, 'v1', '7', outline.points)))
})

spec('ui:review:bake-waits-for-a-stage-and-then-queues', async () => {
  holds('bakeTattoo', await sent(() => bakeTattoo('b', 'bow', ask)))
})

spec('ui:picker:a-refusal-shows-its-fix', async () => {
  answered(502, '<html>bad gateway</html>')
  await expect(keepTattoo('s1', 'bow.png', 'bow')).rejects.toThrow('/api/tattoos answered 502')

  answered(409, JSON.stringify({ refusal: 'name taken' }))
  await expect(keepTattoo('s1', 'bow.png', 'bow')).rejects.toThrow('name taken')
})

spec('ui:draft-from:a-selection-drafts-into-the-flow-chosen', async () => {
  const refused = { refusal: 'x', images: [] }
  answered(409, JSON.stringify(refused))
  await expect(draft('b', place.flow, [])).resolves.toEqual(refused)
})

spec('ui:preview:a-refusal-clears-the-answer-and-shows-its-fix', async () => {
  answered(200, '', { 'X-Ink-White': '128' })
  await expect(inkView('b', 'bow', outline, place)).rejects.toThrow('answered no ink box or white point')
})
