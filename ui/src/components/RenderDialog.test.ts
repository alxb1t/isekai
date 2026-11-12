import { expect } from 'vitest'
import { spec } from '../test/spec'
import {
  confirmReason,
  drawnBakes,
  drawnFlows,
  NOTHING_LEFT,
  ROW_THUMBS,
  thumbs,
  tileMoved,
  tileRow,
} from '../thumbs'

const source = (index: number, images = 1) => ({
  name: `p${index}.jpg`,
  digest: `d${index}`,
  run: `r${index}`,
  version: 1,
  images,
})

spec('ui:render:the-dialog-shows-thumbnails-by-flow', () => {
  const row = thumbs('c', 'summon-anime-wai', Array.from({ length: 17 }, (_, index) => source(index)))
  expect(ROW_THUMBS).toBe(15)
  expect(row.thumbs.map((one) => one.title)).toEqual(
    Array.from({ length: 15 }, (_, index) => `p${index}.jpg v1`),
  )
  expect(row.more).toBe(2)
  expect(thumbs('c', 'summon-anime-wai', [source(0)]).more).toBe(0)
})

spec('ui:render:the-dialog-shows-thumbnails-by-flow', () => {
  const [once, twice] = thumbs('c', 'f', [source(0), source(1, 2)]).thumbs
  expect(once.times).toBeNull()
  expect(twice.times).toBe(2)
})

spec('ui:render:the-dialog-shows-thumbnails-by-flow', () => {
  const [unversioned] = thumbs('c', 'f', [{ ...source(0), version: null }]).thumbs
  expect(unversioned.title).toBe('p0.jpg')
  expect(thumbs('c', 'f', [{ ...source(0), version: 3 }]).thumbs[0].title).toBe('p0.jpg v3')
})

spec('ui:render:the-dialog-shows-thumbnails-by-flow', () => {
  const [one] = thumbs('my c', 'summon-anime-wai', [{ ...source(0), name: 'a b.jpg' }]).thumbs
  expect(one.key).toBe('my c|d0|summon-anime-wai')
  expect(one.src).toBe('/api/c/my%20c/sources/a%20b.jpg/thumb')
  expect(one.fallback).toBe('/api/c/my%20c/review/d0/summon-anime-wai/photo')
})

spec('ui:render:taking-out-shows-the-next', () => {
  const sources = Array.from({ length: 17 }, (_, index) => source(index))
  const row = thumbs('c', 'summon-anime-wai', sources, new Set(['c|d3|summon-anime-wai']))
  expect(row.thumbs.map((one) => one.title)).toEqual(
    [0, 1, 2, ...Array.from({ length: 12 }, (_, index) => index + 4)].map(
      (index) => `p${index}.jpg v1`,
    ),
  )
  expect(row.more).toBe(1)
})

const bake = (index: number, flow = 'f', k = 1) => ({
  ...source(index),
  flow,
  version: 2,
  seed: '7',
  k,
})

spec('ui:render:nothing-left-disables-render', () => {
  const row = {
    collection: 'c',
    images: 2,
    flows: [{ flow: 'f', images: 2, sources: [source(0), source(1)] }],
    bakes: [],
    refused: null,
  }
  expect(NOTHING_LEFT).toBe('Nothing left to render.')
  expect(confirmReason([row], new Set(['c|d0|f', 'c|d1|f']), null)).toBe(NOTHING_LEFT)
  expect(confirmReason([row], new Set(['c|d0|f']), null)).toBeNull()
  // A flow with none left draws no line, so an all-removed row counts no images.
  expect(drawnFlows(row, new Set(['c|d0|f', 'c|d1|f']))).toEqual([])
  expect(drawnFlows(row, new Set(['c|d0|f'])).map((one) => one.thumbs.length)).toEqual([1])
  const none = { ...row, flows: [] }
  expect(confirmReason([none], new Set(), 'refused')).toBe('refused')

  // A bake counts as much as a tile: a row of bakes alone is all out once each is.
  const baked = { ...none, images: 0, bakes: [bake(2), bake(3, 'g')] }
  expect(confirmReason([baked], new Set(['c|d2|f']), null)).toBeNull()
  expect(confirmReason([baked], new Set(['c|d2|f', 'c|d3|g']), null)).toBe(NOTHING_LEFT)
  const both = { ...row, bakes: [bake(2)] }
  expect(confirmReason([both], new Set(['c|d0|f', 'c|d1|f']), null)).toBeNull()
  expect(confirmReason([both], new Set(['c|d0|f', 'c|d1|f', 'c|d2|f']), null)).toBe(NOTHING_LEFT)
})

spec('ui:render:a-photograph-taken-out-takes-its-bakes', () => {
  const row = {
    collection: 'my c',
    images: 1,
    flows: [{ flow: 'f', images: 1, sources: [source(0)] }],
    bakes: [bake(0), bake(0, 'g', 2), bake(1)],
    refused: null,
  }
  expect(drawnBakes(row, new Set()).map((one) => one.label)).toEqual([
    'v2 · 7 · edit 1',
    'v2 · 7 · edit 2',
    'v2 · 7 · edit 1',
  ])
  // The photograph's key, `<collection>|<digest>|<flow>`, takes its bakes of that flow and no other.
  const left = drawnBakes(row, new Set(['my c|d0|f']))
  expect(left.map((one) => [one.key, one.flow])).toEqual([
    ['my c|d0|g', 'g'],
    ['my c|d1|f', 'f'],
  ])
  expect(drawnBakes(row, new Set(['my c|d0|f', 'my c|d0|g', 'my c|d1|f']))).toEqual([])

  // A bake row draws its photograph's thumbnail and name, and takes out its run's flow.
  const [one] = drawnBakes(row, new Set())
  expect(one.title).toBe('p0.jpg')
  expect(one.run).toBe('r0')
  expect(one.src).toBe('/api/c/my%20c/sources/p0.jpg/thumb')
  expect(one.times).toBeNull()
})

spec('ui:render:the-tiles-move-by-flow', () => {
  const moves = [
    [0, 'column+', 1],
    [2, 'column+', 2],
    [0, 'column-', 0],
    [2, 'row+', 4],
    [4, 'row-', 1],
    [1, 'row+', 4],
  ] as const
  for (const [index, move, to] of moves) expect(tileMoved([3, 2], index, move)).toBe(to)
})

spec('ui:render:a-key-move-centres-the-tile', () => {
  // A tile's grid row is its flow's, the edges' rule centring a middle flow's alone.
  const rows = [0, 0, 0, 1, 1, 2, 2, 2, 2]
  for (const [index, row] of rows.entries()) expect(tileRow([3, 2, 4], index)).toBe(row)
})
