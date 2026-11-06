import { expect } from 'vitest'
import { spec } from '../test/spec'
import { confirmReason, NOTHING_LEFT, ROW_THUMBS, thumbs, tileMoved } from '../thumbs'

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

spec('ui:render:nothing-left-disables-render', () => {
  const row = {
    collection: 'c',
    images: 2,
    flows: [{ flow: 'f', images: 2, sources: [source(0), source(1)] }],
    refused: null,
  }
  expect(NOTHING_LEFT).toBe('Nothing left to render.')
  expect(confirmReason([row], new Set(['c|d0|f', 'c|d1|f']), null)).toBe(NOTHING_LEFT)
  expect(confirmReason([row], new Set(['c|d0|f']), null)).toBeNull()
  const none = { ...row, flows: [] }
  expect(confirmReason([none], new Set(), 'refused')).toBe('refused')
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
