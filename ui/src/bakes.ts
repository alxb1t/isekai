import type { Bake } from './types'

/** One row of a render's chain: a bake and the bakes it descends through. */
export interface ChainRow extends Bake {
  depth: number
}

/** Return the rows of a render's chain by number, each with the bakes its `placed_on` chain passes through.

    A `placed_on` naming no row is depth 0, as is a damaged row, which has none.
    e.g. 1 on the render, 2 on 1, 3 on 2 -> depths 0, 1, 2 */
export function chainRows(bakes: readonly Bake[]): ChainRow[] {
  const held = new Map(bakes.map((one) => [one.k, one]))
  const depth = (one: Bake): number => {
    let count = 0
    const seen = new Set([one.k])
    for (let at = one.placed_on; at !== null && held.has(at) && !seen.has(at); ) {
      count += 1
      seen.add(at)
      at = held.get(at)?.placed_on ?? null
    }
    return count
  }
  return [...bakes].sort((a, b) => a.k - b.k).map((one) => ({ ...one, depth: depth(one) }))
}

/** Return whether the large view offers *Draft from this*, *Compare with…* and *Delete*: on a render's address, `k` absent.

    e.g. undefined -> true, "1" -> false */
export const offered = (k: string | undefined): boolean => k === undefined
