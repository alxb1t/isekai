import { expect } from 'vitest'
import { chainRows, offered } from './bakes'
import { spec } from './test/spec'
import type { Bake } from './types'

const bake = (k: number, placed_on: number | null, state: Bake['state'] = 'baked'): Bake => ({
  k,
  state,
  placed_on,
  baked_at: state === 'baked' ? 1_700_000_000 : null,
  edit: state === 'damaged' ? null : 'tattoo',
  reason: state === 'damaged' ? 'edit 3 is damaged' : null,
})

spec('ui:bakes:the-chain-lists-the-bakes-in-order', () => {
  const rows = chainRows([bake(3, 2, 'queued'), bake(1, null), bake(2, 1)])
  expect(rows.map((row) => [row.k, row.state, row.depth])).toEqual([
    [1, 'baked', 0],
    [2, 'baked', 1],
    [3, 'queued', 2],
  ])

  // Bakes placed on one image are siblings at one depth.
  expect(chainRows([bake(1, null), bake(2, 1), bake(3, 1)]).map((row) => row.depth)).toEqual([0, 1, 1])

  // A `placed_on` naming no row is depth 0, and a damaged row ends its chain.
  expect(chainRows([bake(4, 9)]).map((row) => row.depth)).toEqual([0])
  const damaged = chainRows([bake(1, null), bake(2, null, 'damaged'), bake(3, 2)])
  expect(damaged.map((row) => row.depth)).toEqual([0, 0, 1])

  // A chain that loops on itself ends rather than hangs.
  expect(chainRows([bake(1, 2), bake(2, 1)]).map((row) => row.depth)).toEqual([1, 1])
  expect(chainRows([])).toEqual([])
})

spec('ui:bakes:a-bakes-view-offers-no-writes', () => {
  expect(offered(undefined)).toBe(true)
  expect(offered('1')).toBe(false)
})
