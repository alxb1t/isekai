/* The Renders grid's moves (D25): `h l` and the arrows step through a row's images,
   crossing its cells, `j k` between rows. A row is a source; a focus column counts
   its source, column 0, then its images across its cells. */

/** A focus on the grid: a source's row and a column in it. */
export interface Focus {
  row: number
  column: number
}

/** A move: to the previous or next image, or row. */
export type Move = 'image-' | 'image+' | 'row-' | 'row+'

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
 * Return the focus after `move`; `images[row]` counts the row's images.
 *
 * A move past either end stays. An image move crosses cells, and reaches the
 * source at a row's start; a row move keeps the column, held at a shorter row's end.
 * e.g. images [3, 2], {row 0, column 3}: 'row+' -> {row 1, column 2}
 */
export function moved(images: number[], at: Focus, move: Move): Focus {
  if (images.length === 0) return at
  const step = move.endsWith('+') ? 1 : -1
  if (move.startsWith('image'))
    return { row: at.row, column: clamp(at.column + step, images[at.row] ?? 0) }
  const row = clamp(at.row + step, images.length - 1)
  return { row, column: clamp(at.column, images[row] ?? 0) }
}
