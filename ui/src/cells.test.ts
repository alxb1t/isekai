import { expect } from 'vitest'
import {
  DONE,
  EMPTY_CELL,
  RUNNING,
  SEGMENTS,
  action,
  cellGrid,
  cellOrder,
  changesOf,
  clicks,
  gridColumns,
  hintOf,
  locked,
  moveCell,
  movePick,
  pending,
  pickHead,
  placeOf,
  ready,
  rowOrder,
  segmentClass,
  sourceGrid,
  stepped,
  targets,
  tileCaption,
  wordOf,
} from './cells'
import { spec } from './test/spec'
import type { HubCell, HubSource, RenderDetail } from './types'

function cell(stage: HubCell['stage'], newest: HubCell['newest'] = null): HubCell {
  return { ...EMPTY_CELL, stage, newest }
}

function sourceOf(name: string, cells: Record<string, HubCell>): HubSource {
  return { name, digest: null, width: null, height: null, cells, carries: [] }
}

const track = (running: string | undefined, one: HubCell): string[] =>
  SEGMENTS.map((_, index) => segmentClass(one, running, index))

spec('ui:prepare:prepare-takes-the-cells-with-no-sheet', () => {
  const ada = sourceOf('ada.jpg', {
    a: cell('assigned'),
    b: cell('tagged'),
    c: cell('sheet'),
  })
  const bea = sourceOf('bea.jpg', { a: cell('unreadable'), b: cell('assigned') })
  // Source by source, flow by flow: the assigned and the tagged cells, never a sheeted
  // or an unreadable one, and a flow the source holds no cell for is none.
  expect(changesOf([ada, bea], ['a', 'b', 'c'])).toEqual([
    { source: ada, flow: 'a' },
    { source: ada, flow: 'b' },
    { source: bea, flow: 'b' },
  ])
})

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
  // A review or a sheet offers its hint only where the source has a run and the cell a status.
  const run = { ...sourceOf('ada.jpg', {}), digest: '0d4b' }
  const bare = sourceOf('bea.jpg', {})
  const sheeted = { ...cell('sheet'), status: 'draft' as const }
  expect(hintOf(run, sheeted)).toBe('↵ review')
  expect(hintOf(bare, sheeted)).toBeNull()
  expect(hintOf(run, cell('sheet'))).toBeNull()
  expect(hintOf(run, cell('approved', image))).toBe('↵ view')
  expect(hintOf(run, cell('tagged'))).toBeNull()
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

spec('ui:hub:a-cells-stage-comes-from-its-run', () => {
  expect(SEGMENTS).toEqual(['assigned', 'tag', 'caption', 'sheet', 'approved', 'rendered'])
  expect(DONE).toEqual({
    assigned: 1,
    tagged: 2,
    sheet: 4,
    draft: 4,
    approved: 5,
    rendered: 6,
    unreadable: 0,
  })
  // With nothing running, a stage marks the segments it has done and no other.
  const counts: [HubCell['stage'], number][] = [
    [null, 0],
    ['assigned', 1],
    ['tagged', 2],
    ['sheet', 4],
    ['draft', 4],
    ['approved', 5],
    ['rendered', 6],
    ['unreadable', 0],
  ]
  for (const [stage, count] of counts) {
    const done = SEGMENTS.map((_, index) => (index < count ? 'hub__segment--done' : ''))
    expect(track(undefined, cell(stage))).toEqual(done)
  }
  // A cell shows its stage, `rendered ×n` once rendered, and nothing with no stage.
  for (const [stage] of counts) {
    if (stage !== null && stage !== 'rendered') expect(wordOf(cell(stage), undefined)).toBe(stage)
  }
  expect(wordOf(cell(null), undefined)).toBe('')
  expect(wordOf(cell('rendered'), undefined)).toBe('rendered ×0')
  expect(wordOf({ ...cell('rendered'), renders: 2 }, undefined)).toBe('rendered ×2')
})

spec('ui:events:a-stages-report-reaches-the-stream', () => {
  expect(RUNNING).toEqual({
    tag: { segment: 1, word: 'tagging…' },
    caption: { segment: 2, word: 'captioning…' },
    sheet: { segment: 3, word: 'filling the sheet…' },
  })
  for (const verb of ['tag', 'caption', 'sheet'] as const) {
    expect(SEGMENTS[RUNNING[verb].segment]).toBe(verb)
  }
  // A running stage shows its word and its segment running, over the done mark of its own.
  expect(wordOf(cell('tagged'), 'caption')).toBe('captioning…')
  expect(track('caption', cell('tagged'))).toEqual([
    'hub__segment--done',
    'hub__segment--done',
    'hub__segment--running',
    '',
    '',
    '',
  ])
  expect(segmentClass(cell('sheet'), 'sheet', 3)).toBe('hub__segment--running')
  expect(track('tag', cell(null))).toEqual(['', 'hub__segment--running', '', '', '', ''])
  // A stage the table lacks shows as `<stage>…` and marks no segment running, `toString` too.
  expect(wordOf(cell('tagged'), 'review')).toBe('review…')
  expect(wordOf(cell('tagged'), 'toString')).toBe('toString…')
  const tagged = ['hub__segment--done', 'hub__segment--done', '', '', '', '']
  expect(track('toString', cell('tagged'))).toEqual(tagged)
  // An empty running stage reads as none.
  expect(wordOf(cell('tagged'), '')).toBe('tagged')
  expect(track('', cell('tagged'))).toEqual(tagged)
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
