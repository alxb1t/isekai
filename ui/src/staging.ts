import { type Move, moved } from './grid'
import type { StagedFile } from './types'

/* An import's staging folder, and when the sheet discards it. A closed sheet
   cancels its folder once no commit is moving it: at closing, or when a commit
   in flight then is refused. Its tiles are a grid the keys step through (D3). */

/** Whether the sheet cancels `staging` now. e.g. ('s1', true, true, false) -> false */
export function discards(
  staging: string | null,
  closed: boolean,
  committing: boolean,
  committed: boolean,
): boolean {
  return staging !== null && closed && !committing && !committed
}

/** Return where removing a tile takes its file from: the staging folder, the sheet alone, or nowhere.

    A skipped file staged nothing of its own; one still on its way offers no removal.
    e.g. ('read', 'skipped') -> 'sheet' */
export function removal(phase: string, state: string | undefined): 'staging' | 'sheet' | null {
  if (phase !== 'read') return null
  return state === 'skipped' ? 'sheet' : 'staging'
}

/** Return the index of the first result skipped as a copy of the staged file `name`, or -1.

    Removing a file a copy still stands for hands the file to that copy, so the
    photograph stays chosen and in the import. e.g. ([{ state: 'skipped', copyOf: 'b.jpg' }], 'b.jpg') -> 0 */
export function heir(results: (StagedFile | null)[], name: string): number {
  return results.findIndex((one) => one?.state === 'skipped' && one.copyOf === name)
}

/** Return the indices of the results skipped as a copy of a file no other result holds.

    A file removed just as its copy is read leaves that copy standing for bytes
    staged nowhere, so the sheet sends it again. e.g. ([{ state: 'skipped', copyOf: 'b.jpg' }]) -> [0] */
export function orphans(results: (StagedFile | null)[]): number[] {
  const held = new Set(results.flatMap((one) => (one && one.state !== 'skipped' ? [one.name] : [])))
  return results.flatMap((one, index) =>
    one?.state === 'skipped' && one.copyOf !== null && !held.has(one.copyOf) ? [index] : [],
  )
}

/** Return the tile the focus takes once the tile at `index` of `count` is removed, or null.

    e.g. (3, 4) -> 2, the last tile's removal passing the focus back */
export function after(index: number, count: number): number | null {
  return count <= 1 ? null : Math.min(index, count - 2)
}

/** Return the tile after `move` from `index`, of `count` tiles laid `columns` to a row.

    Unmeasured, `columns` is 0 and the tiles are one row. e.g. (2, 5, 3, 'row+') -> 4 */
export function stepped(index: number, count: number, columns: number, move: Move): number {
  if (count === 0) return index
  const wide = columns > 0 ? columns : count
  const last = Array.from({ length: Math.ceil(count / wide) }, (_, row) =>
    Math.min(wide, count - row * wide) - 1,
  )
  const to = moved(last, { row: Math.floor(index / wide), column: index % wide }, move)
  return to.row * wide + to.column
}
