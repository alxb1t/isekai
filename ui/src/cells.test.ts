import { expect } from 'vitest'
import {
  EMPTY_CELL,
  action,
  clicks,
  movePick,
  pickHead,
  placeOf,
  screenOrder,
  sourceGrid,
  stepped,
  targets,
  tileCaption,
} from './cells'
import { spec } from './test/spec'
import type { HubCell, RenderDetail } from './types'

function cell(stage: HubCell['stage'], newest: HubCell['newest'] = null): HubCell {
  return { ...EMPTY_CELL, stage, newest }
}

spec('ui:hub:a-click-follows-the-cells-stage', () => {
  const image = { version: 1, seed: '7' }
  const cases: [HubCell, string, string | null][] = [
    [cell(null), 'tick', null],
    [cell('assigned'), 'tick', null],
    [cell('tagged'), 'none', null],
    [cell('unreadable'), 'none', null],
    [cell('sheet'), 'review', '↵ review'],
    [cell('draft'), 'review', '↵ review'],
    [cell('approved'), 'sheet', '↵ review'],
    [cell('approved', image), 'view', '↵ view'],
    [cell('rendered', image), 'view', '↵ view'],
  ]
  for (const [one, kind, hint] of cases) {
    expect(action(one)).toEqual({ action: kind, hint })
  }
  // A click ticks the cell it lands on, whatever rows ⇧↑↓ selected; space ticks
  // the selection.
  expect(targets(new Set([1, 2, 3]), 6, true)).toEqual([6])
  expect(targets(new Set([1, 2, 3]), 6, false)).toEqual([1, 2, 3])
  expect(targets(new Set(), 6, false)).toEqual([6])
  // A click on a refusal, or one that ends a text selection, is reading, not acting.
  const on = (refusal: boolean) => ({ closest: () => (refusal ? {} : null) })
  expect(clicks(on(false), '')).toBe(true)
  expect(clicks(on(true), '')).toBe(false)
  expect(clicks(on(false), 'python -m isekai')).toBe(false)
})

spec('ui:compare:the-pick-moves-by-row-and-column', () => {
  const summon = [
    { version: 1, seed: '7' },
    { version: 2, seed: '5' },
    { version: 3, seed: '7' },
  ]
  const detail = {
    flow: 'summon-anime-wai',
    version: 3,
    seed: '7',
    compare: null,
    source: [
      { flow: 'summon-anime-wai', images: summon },
      { flow: 'summon-flat-anime-wai', images: [{ version: 1, seed: '5' }] },
    ],
  } as unknown as RenderDetail
  const grid = sourceGrid(detail)
  expect(grid.origin).toEqual({ row: 1, column: 2 })

  const down = movePick(grid, { row: 0, column: 0 }, 'row+')
  const across = movePick(grid, movePick(grid, down, 'column+'), 'column+')
  const shorter = movePick(grid, across, 'row+')

  expect(down).toEqual({ row: 1, column: 0 })
  expect(across).toEqual({ row: 1, column: 2 })
  expect(shorter).toEqual({ row: 2, column: 0 })
})

spec('ui:compare:a-seed-pairs-with-its-newest-older-version', () => {
  const opened = (version: number, compare: number | null, images: [number, string][]) =>
    sourceGrid({
      flow: 'summon-anime-wai',
      version,
      seed: '7',
      compare,
      source: [
        {
          flow: 'summon-anime-wai',
          images: images.map(([one, seed]) => ({ version: one, seed })),
        },
      ],
    } as unknown as RenderDetail).start

  // The seed's newest older version, past the image before it of another seed.
  expect(
    opened(3, 1, [
      [1, '7'],
      [2, '5'],
      [3, '7'],
    ]),
  ).toEqual({ row: 1, column: 0 })
  // Else the image before it in its row.
  expect(
    opened(2, null, [
      [1, '5'],
      [2, '7'],
    ]),
  ).toEqual({ row: 1, column: 0 })
  // Else, first in its row, the photograph.
  expect(
    opened(1, null, [
      [1, '7'],
      [2, '5'],
    ]),
  ).toEqual({ row: 0, column: 0 })
})

spec('ui:compare:the-pick-names-the-focused-tile', () => {
  const seed = '18446744073709551615'
  const grid = sourceGrid({
    flow: 'summon-anime-wai',
    version: 3,
    seed: '7',
    compare: null,
    source: [
      {
        flow: 'summon-anime-wai',
        images: [
          { version: 2, seed: '7' },
          { version: 2, seed },
          { version: 3, seed: '7' },
        ],
      },
    ],
  } as unknown as RenderDetail)
  const second = movePick(grid, { row: 1, column: 0 }, 'column+')
  const tile = grid.rows[second.row].tiles[second.column]

  expect(tileCaption(tile)).toBe('v2')
  expect(pickHead({ flow: 'summon-anime-wai', version: 3, seed: '7' }, tile)).toBe(
    `Compare summon-anime-wai v3 · seed 7 with summon-anime-wai v2 · seed ${seed}…`,
  )
})

spec('ui:renders:the-large-view-steps-its-screens-order', () => {
  const detail = {
    flow: 'summon-anime-wai',
    version: 1,
    seed: '7',
    source: [
      {
        flow: 'summon-anime-wai',
        images: [
          { version: 1, seed: '7' },
          { version: 2, seed: '7' },
        ],
      },
      { flow: 'summon-flat-anime-wai', images: [{ version: 1, seed: '5' }] },
    ],
  } as unknown as RenderDetail
  const first = { flow: 'summon-anime-wai', version: 1, seed: '7' }
  const second = { flow: 'summon-anime-wai', version: 2, seed: '7' }
  const flat = { flow: 'summon-flat-anime-wai', version: 1, seed: '5' }

  // From Renders, the row runs on across the flows; at its last image l holds.
  const row = screenOrder(detail, 'renders')
  expect(stepped(row, first, 1)).toEqual(second)
  expect(stepped(row, second, 1)).toEqual(flat)
  expect(stepped(row, flat, 1)).toBeNull()
  expect(stepped(row, first, -1)).toBeNull()
  detail.cell = detail.source[0].images
  // From the hub, the cell's images alone.
  const cell = screenOrder(detail, 'hub')
  expect(stepped(cell, first, 1)).toEqual(second)
  expect(stepped(cell, second, 1)).toBeNull()

  // One approval's seeds were written 9 then 2; Renders sorts them numerically.
  const nine = { flow: detail.flow, version: 1, seed: '9' }
  const two = { flow: detail.flow, version: 1, seed: '2' }
  detail.source[0].images = [two, nine]
  detail.cell = [nine, two]
  const hub = screenOrder(detail, 'hub')
  expect(stepped(hub, nine, 1)).toEqual(two)
  expect(stepped(hub, two, 1)).toBeNull()
  expect(placeOf(hub, two)).toBe(1)
  expect(stepped(screenOrder(detail, 'renders'), two, 1)).toEqual(nine)
})
