import { expect } from 'vitest'
import { first, grid, stepped } from './sessions'
import { spec } from './test/spec'
import type { SessionRecord } from './types'

const SUMMON = 'summon-anime-wai'
const CONJURE = 'conjure-anime-wai'

/* A record of `images` landed, planning `planned` where given. */
function record(given: Partial<SessionRecord>): SessionRecord {
  return {
    id: '20261024T091200Z',
    started: '2026-10-24T09:12:00Z',
    ended: null,
    limit: 1200,
    asked: {},
    steps: {},
    images: [],
    outcome: 'running',
    message: null,
    ...given,
  }
}

const image = (digest: string, flow: string, seed: string) => ({ digest, flow, version: 1, seed })

spec('ui:sessions:the-grid-holds-each-flow-over-the-originals', () => {
  const planned = record({
    planned: [
      { digest: 'a', flow: SUMMON, images: 2 },
      { digest: 'b', flow: CONJURE, images: 1 },
    ],
  })

  const held = grid(planned)

  expect(held.digests).toEqual(['a', 'b'])
  expect(held.flows).toEqual([SUMMON, CONJURE])
  expect(held.cells.flat().map((cell) => cell.waiting)).toEqual([2, 0, 0, 1])
  expect(held.cells.flat().reduce((sum, cell) => sum + cell.waiting, 0)).toBe(3)

  // A landed image takes a waiting tile's place.
  const landing = grid({ ...planned, images: [image('a', SUMMON, '7')] })
  expect(landing.cells[0][0]).toEqual({ images: [image('a', SUMMON, '7')], waiting: 1 })

  // A record without a plan places what landed, and waits for nothing.
  const older = grid(record({ images: [image('a', SUMMON, '7'), image('b', SUMMON, '8')] }))
  expect(older.digests).toEqual(['a', 'b'])
  expect(older.flows).toEqual([SUMMON])
  expect(older.cells[0].map((cell) => [cell.images.length, cell.waiting])).toEqual([
    [1, 0],
    [1, 0],
  ])
})

spec('ui:sessions:the-grid-moves-by-photograph-and-row', () => {
  const landed = record({
    planned: [
      { digest: 'a', flow: SUMMON, images: 1 },
      { digest: 'b', flow: SUMMON, images: 1 },
      { digest: 'b', flow: CONJURE, images: 1 },
    ],
    images: [image('a', SUMMON, '7')],
  })
  const held = grid(landed)
  const start = first(held, landed)
  expect(start).toEqual({ row: 0, column: 0 })

  const right = stepped(held, start, 'photograph+')
  expect(right).toEqual({ row: 0, column: 1 })
  const down = stepped(held, right, 'row+')
  expect(down).toEqual({ row: 1, column: 1 })
  // Row 2 is the photographs' row: the last, where a row move stops.
  const photographs = stepped(held, down, 'row+')
  expect(photographs).toEqual({ row: 2, column: 1 })
  expect(stepped(held, photographs, 'row+')).toEqual(photographs)
  expect(stepped(held, right, 'photograph+')).toEqual(right)
  expect(stepped(held, start, 'row-')).toEqual(start)
})
