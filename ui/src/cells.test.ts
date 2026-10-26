import { expect } from 'vitest'
import { EMPTY_CELL, action, clicks, pick, targets } from './cells'
import { spec } from './test/spec'
import type { HubCell } from './types'

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

spec('ui:compare:one-other-image-is-compared-at-once', () => {
  const v1 = { version: 1, seed: '7' }
  const v2 = { version: 2, seed: '7' }
  // One other image: no pick.
  expect(pick([v1, v2], 2, '7', 1)).toEqual({ compare: v1 })

  // Three others: the pick opens on v2, this seed's newest older version.
  const v2b = { version: 2, seed: '5' }
  const v3 = { version: 3, seed: '7' }
  expect(pick([v1, v2, v2b, v3], 3, '7', 2)).toEqual({ at: 1 })
  // With no older version of the seed, on the image before this one.
  expect(pick([v1, v2b, v3], 3, '7', null)).toEqual({ at: 1 })
})
