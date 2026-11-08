import { expect } from 'vitest'
import { cellGrid, moveCell } from './cells'
import { spec } from './test/spec'

spec('ui:keys:a-row-move-keeps-the-column', () => {
  // The cell modal's third image of a row whose next row holds two.
  const images = ['1', '2', '3', '4', '5'].map((seed) => ({ version: 1, seed }))
  const grid = cellGrid('summon-anime-wai', images, images[0])
  const third = { row: 0, column: 2 }

  expect(moveCell(grid, third, 'row+')).toEqual({ row: 1, column: 1 })
  expect(moveCell(grid, { row: 1, column: 1 }, 'row-')).toEqual({ row: 0, column: 1 })
})
