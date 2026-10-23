/* The Renders grid's moves (D25): `h j k l` between cells, the arrows between images.
   A row is a source; its cells are its flows, each a run of images, and a focus
   column counts a row's images across its cells. */

/** A focus on the grid: a source's row and an image's column in it. */
export interface Focus {
  row: number
  column: number
}

/** A move: to the previous or next cell, image or row. */
export type Move = 'cell-' | 'cell+' | 'image-' | 'image+' | 'row-' | 'row+'

const clamp = (value: number, high: number) => Math.min(Math.max(value, 0), high)

/* The cell a column falls in, and the column its first image takes. */
function cellOf(counts: number[], column: number): { cell: number; start: number } {
  let start = 0
  for (const [cell, count] of counts.entries()) {
    if (column < start + count) return { cell, start }
    start += count
  }
  return { cell: counts.length - 1, start: start - (counts.at(-1) ?? 0) }
}

const startOf = (counts: number[], cell: number) =>
  counts.slice(0, cell).reduce((sum, count) => sum + count, 0)

const total = (counts: number[]) => startOf(counts, counts.length)

/**
 * Return the focus after `move`; `cells[row][cell]` counts each cell's images.
 *
 * A move past either end stays, and an empty cell or row is stepped over.
 * e.g. cells [[2, 3]], {row 0, column 0}: 'cell+' -> column 2, 'image+' -> column 1
 */
export function moved(cells: number[][], at: Focus, move: Move): Focus {
  const counts = cells[at.row] ?? []
  const here = cellOf(counts, at.column)
  const step = move.endsWith('+') ? 1 : -1
  if (move.startsWith('image')) {
    const column = clamp(at.column - here.start + step, counts[here.cell] - 1) + here.start
    return { row: at.row, column }
  }
  if (move.startsWith('cell')) {
    for (let cell = here.cell + step; cell >= 0 && cell < counts.length; cell += step)
      if (counts[cell] > 0) return { row: at.row, column: startOf(counts, cell) }
    return at
  }
  for (let row = at.row + step; row >= 0 && row < cells.length; row += step) {
    if (total(cells[row]) === 0) continue
    return { row, column: clamp(at.column, total(cells[row]) - 1) }
  }
  return at
}
