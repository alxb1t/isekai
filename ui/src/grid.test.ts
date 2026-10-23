import { expect } from 'vitest'
import { moved } from './grid'
import { spec } from './test/spec'

spec('ui:keys:renders-moves-by-cell-and-by-image', () => {
  // One source over three flows: two images, none, three.
  const cells = [
    [2, 0, 3],
    [0, 0, 0],
    [1, 1, 1],
  ]
  const start = { row: 0, column: 0 }

  const cell = moved(cells, start, 'cell+')
  expect(cell).toEqual({ row: 0, column: 2 })
  expect(moved(cells, cell, 'image+')).toEqual({ row: 0, column: 3 })
  expect(moved(cells, start, 'image+')).toEqual({ row: 0, column: 1 })
  // An image move stays inside its cell; a cell move steps over an empty one.
  expect(moved(cells, { row: 0, column: 1 }, 'image+')).toEqual({ row: 0, column: 1 })
  expect(moved(cells, cell, 'cell-')).toEqual({ row: 0, column: 0 })
  expect(moved(cells, { row: 0, column: 4 }, 'row+')).toEqual({ row: 2, column: 2 })

  // A row move keeps the flow: its image, or the last the next row has in it.
  const uneven = [
    [5, 2],
    [10, 2],
    [0, 1],
  ]
  expect(moved(uneven, { row: 0, column: 5 }, 'row+')).toEqual({ row: 1, column: 10 })
  expect(moved(uneven, { row: 1, column: 11 }, 'row-')).toEqual({ row: 0, column: 6 })
  expect(moved(uneven, { row: 1, column: 7 }, 'row+')).toEqual({ row: 2, column: 0 })
})
