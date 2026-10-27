import { expect } from 'vitest'
import { EMPTY_CELL, action, clicks, movePick, sourceGrid, targets } from './cells'
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
