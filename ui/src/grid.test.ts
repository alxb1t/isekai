import { expect } from 'vitest'
import { moved } from './grid'
import { spec } from './test/spec'

spec('ui:keys:renders-moves-by-cell-and-by-image', () => {
  // Three sources; a column counts the source, 0, then the row's images across its
  // cells: the first row's two, none and three images are its columns 1 to 5.
  const images = [5, 0, 3]
  const last = { row: 0, column: 2 }

  // h l and the arrows both step images, crossing from a cell's last to the next's first.
  expect(moved(images, last, 'column+')).toEqual({ row: 0, column: 3 })
  expect(moved(images, { row: 0, column: 3 }, 'column-')).toEqual(last)
  // A row's start steps into its source, and no further; its end stays.
  expect(moved(images, { row: 0, column: 1 }, 'column-')).toEqual({ row: 0, column: 0 })
  expect(moved(images, { row: 0, column: 0 }, 'column-')).toEqual({ row: 0, column: 0 })
  expect(moved(images, { row: 0, column: 5 }, 'column+')).toEqual({ row: 0, column: 5 })
  // A source with no images is still its row's spot.
  expect(moved(images, { row: 1, column: 0 }, 'column+')).toEqual({ row: 1, column: 0 })
  expect(moved([], { row: 0, column: 0 }, 'row+')).toEqual({ row: 0, column: 0 })
})

spec('ui:keys:a-row-move-keeps-the-column', () => {
  // The third image of a row whose next row holds two.
  const images = [4, 2, 6]
  const third = { row: 0, column: 3 }

  expect(moved(images, third, 'row+')).toEqual({ row: 1, column: 2 })
  expect(moved(images, { row: 2, column: 5 }, 'row-')).toEqual({ row: 1, column: 2 })
  expect(moved(images, { row: 1, column: 1 }, 'row+')).toEqual({ row: 2, column: 1 })
  // The source column stays the source column; past either end the focus stays.
  expect(moved(images, { row: 1, column: 0 }, 'row+')).toEqual({ row: 2, column: 0 })
  expect(moved(images, third, 'row-')).toEqual(third)
  expect(moved(images, { row: 2, column: 5 }, 'row+')).toEqual({ row: 2, column: 5 })
})
