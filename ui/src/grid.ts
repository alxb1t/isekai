/* A grid's moves (D25): `h l` and the arrows step along a row, `j k` between rows.
   On Renders a row is a source, and a focus column counts its source, column 0,
   then its images across its cells; the render drawer's grid is rectangular. */

/** A focus on the grid: a source's row and a column in it. */
export interface Focus {
  row: number
  column: number
}

/** A move: to the previous or next column, or row. */
export type Move = 'column-' | 'column+' | 'row-' | 'row+'

/** Return `value` held between 0 and `high`. */
export const clamp = (value: number, high: number) => Math.min(Math.max(value, 0), high)

/** Return the spot of `spots` that `name` calls `held`, else the first.

    A remembered focus can outlive its spot, as a source is added or a version
    rendered. e.g. kept(['a', 'c'], (one) => one, 'b') -> 'a' */
export function kept<T>(
  spots: T[],
  name: (spot: T) => string,
  held: string | null,
): T | undefined {
  return spots.find((one) => name(one) === held) ?? spots[0]
}

/**
 * Return the focus after `move`; `last[row]` is the row's last column.
 *
 * A move past either end stays; a row move keeps the column, held at a shorter
 * row's end. e.g. last [3, 2], {row 0, column 3}: 'row+' -> {row 1, column 2}
 */
export function moved(last: number[], at: Focus, move: Move): Focus {
  if (last.length === 0) return at
  const step = move.endsWith('+') ? 1 : -1
  if (move.startsWith('column'))
    return { row: at.row, column: clamp(at.column + step, last[at.row] ?? 0) }
  const row = clamp(at.row + step, last.length - 1)
  return { row, column: clamp(at.column, last[row] ?? 0) }
}
