import { expect } from 'vitest'
import {
  EMPTY_CELL,
  action,
  cellGrid,
  cellOrder,
  clicks,
  gridColumns,
  locked,
  moveCell,
  movePick,
  pending,
  pickHead,
  placeOf,
  ready,
  rowOrder,
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
    [cell('tagged'), 'tick', null],
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

spec('ui:hub:a-tagged-cell-with-no-work-unticks', () => {
  const stages: HubCell['stage'][] = [
    null,
    'assigned',
    'tagged',
    'sheet',
    'draft',
    'approved',
    'rendered',
    'unreadable',
  ]
  expect(stages.map((stage) => pending(cell(stage)))).toEqual([
    false,
    true,
    true,
    false,
    false,
    false,
    false,
    false,
  ])
  expect(stages.map((stage) => locked(cell(stage)))).toEqual([
    false,
    false,
    false,
    true,
    true,
    true,
    true,
    true,
  ])
})

spec('ui:hub:the-cell-modal-moves-by-version-and-seed', () => {
  const flow = 'summon-anime-wai'
  const images = [
    { version: 1, seed: '9' },
    { version: 1, seed: '2' },
    { version: 2, seed: '4' },
    { version: 2, seed: '6' },
    { version: 2, seed: '8' },
  ]
  // The cell's thumbnails and the modal stand in one order: versions oldest
  // first, seeds as numbers, past a number's safe range too.
  expect(cellOrder(images)).toEqual([images[1], images[0], images[2], images[3], images[4]])
  expect(
    cellOrder([
      { version: 1, seed: '18446744073709551615' },
      { version: 1, seed: '18446744073709551614' },
      { version: 1, seed: '9' },
    ]).map((one) => one.seed),
  ).toEqual(['9', '18446744073709551614', '18446744073709551615'])

  const grid = cellGrid(flow, images, { version: 1, seed: '9' })
  expect(grid.rows).toEqual([
    {
      tiles: [
        { flow, version: 1, seed: '2' },
        { flow, version: 1, seed: '9' },
        { flow, version: 2, seed: '4' },
      ],
    },
    {
      tiles: [
        { flow, version: 2, seed: '6' },
        { flow, version: 2, seed: '8' },
      ],
    },
  ])
  expect(grid.start).toEqual({ row: 0, column: 1 })
  // l at a row's end goes on to the next row's first, and h comes back.
  expect(moveCell(grid, { row: 0, column: 2 }, 'column+')).toEqual({ row: 1, column: 0 })
  expect(moveCell(grid, { row: 1, column: 0 }, 'column-')).toEqual({ row: 0, column: 2 })
  // j onto a missing tile lands on the shorter row's last.
  expect(moveCell(grid, { row: 0, column: 2 }, 'row+')).toEqual({ row: 1, column: 1 })
  // At the grid's ends the focus holds.
  expect(moveCell(grid, { row: 1, column: 1 }, 'column+')).toEqual({ row: 1, column: 1 })
  expect(moveCell(grid, { row: 0, column: 0 }, 'column-')).toEqual({ row: 0, column: 0 })
})

spec('ui:hub:the-cell-modal-balances-its-rows', () => {
  const lengths = (count: number) =>
    cellGrid(
      'summon-anime-wai',
      Array.from({ length: count }, (_, seed) => ({ version: 1, seed: `${seed}` })),
      { version: 1, seed: '0' },
    ).rows.map((one) => one.tiles.length)
  expect([1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(lengths)).toEqual([
    [1],
    [2],
    [3],
    [2, 2],
    [3, 2],
    [3, 3],
    [3, 3, 1],
    [3, 3, 2],
    [3, 3, 3],
    [3, 3, 3, 1],
  ])
  expect(gridColumns(0)).toBe(0)
})

spec('ui:hub:a-seed-under-two-versions-is-marked', () => {
  const grid = cellGrid(
    'summon-anime-wai',
    [
      { version: 1, seed: '7' },
      { version: 2, seed: '5' },
      { version: 2, seed: '7' },
    ],
    { version: 2, seed: '7' },
  )
  expect(grid.shared.has('7')).toBe(true)
  expect(grid.shared.has('5')).toBe(false)
  expect(grid.start).toEqual({ row: 0, column: 2 })
})

spec('ui:hub:a-cell-shows-what-is-ready', () => {
  const lacking = (short: number | null) => ready({ ...EMPTY_CELL, stage: 'rendered', short })
  expect(lacking(2)).toBe('ready · 2 images')
  expect(lacking(1)).toBe('ready · 1 image')
  expect(lacking(0)).toBeNull()
  expect(lacking(null)).toBeNull()
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
  expect(pickHead({ flow: 'summon-anime-wai', version: 3, seed: '7' }, tile)).toEqual([
    'Compare summon-anime-wai v3 · seed 7',
    `with summon-anime-wai v2 · seed ${seed}`,
  ])
})

spec('ui:renders:the-large-view-walks-the-photographs-row', () => {
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

  // The row runs on across the flows, in the hub's column order; at its last image l holds.
  const row = rowOrder(detail)
  expect(stepped(row, first, 1)).toEqual(second)
  expect(stepped(row, second, 1)).toEqual(flat)
  expect(stepped(row, flat, 1)).toBeNull()
  expect(stepped(row, first, -1)).toBeNull()
  expect(placeOf(row, flat)).toBe(2)
})
