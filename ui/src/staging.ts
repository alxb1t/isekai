import { type Move, moved } from './grid'
import type { StagedFile } from './types'
import { noun } from './words'

/* An import's staging folder, and when the sheet discards it. A closed sheet
   cancels its folder once no commit is moving it: at closing, or when a commit
   in flight then is refused. Its tiles are a grid the keys step through, as on every grid. */

/* `queued` before its upload starts; `waiting` and `converting` are the server's. */
export type Phase = 'queued' | 'uploading' | 'waiting' | 'converting' | 'read' | 'refused'

export interface Tile {
  key: number
  file: File
  /* The server's id for this upload, once its request is answered. */
  upload: string | null
  phase: Phase
  progress: number
  result: StagedFile | null
  refusal: string | null
  asIs: boolean
}

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

    A skipped file staged nothing of its own; one still on its way, or `leaving`
    by a removal in flight, offers no removal. e.g. ('read', 'skipped') -> 'sheet' */
export function removal(
  phase: string,
  state: string | undefined,
  leaving = false,
): 'staging' | 'sheet' | null {
  if (phase !== 'read' || leaving) return null
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

/** Return the staged name removing `one` takes from the folder, or null when a copy takes it over.

    The first copy `heir` finds gets `one`'s upload, result and choice; with no
    result there is nothing staged to name. e.g. a tile of 'b.jpg', no copy -> 'b.jpg' */
export function handOff(tiles: Tile[], one: Tile): string | null {
  if (!one.result) return null
  const copy = tiles[heir(tiles.map((tile) => tile.result), one.result.name)]
  if (!copy) return one.result.name
  copy.upload = one.upload
  copy.result = one.result
  copy.asIs = one.asIs
  return null
}

/** Return the tiles `orphans` names, each cleared and queued to be sent again. */
export function requeue(tiles: Tile[]): Tile[] {
  const lost = orphans(tiles.map((tile) => tile.result)).map((index) => tiles[index])
  for (const one of lost) {
    one.upload = null
    one.phase = 'queued'
    one.progress = 0
    one.result = null
  }
  return lost
}

/** What Import's state is read from: the tiles chosen, read and ready, and the removals in flight. */
export interface Sheet {
  committing: boolean
  removing: number
  chosen: number
  read: number
  ready: number
  adding: boolean
}

/** Return Import's reason for being disabled, or null when it is not (rule 4).

    A removal in flight holds Import until its tile is gone, so a copy it leaves
    standing for bytes staged nowhere is sent again before the commit.
    e.g. ({ committing: false, removing: 1, chosen: 2, read: 2, ready: 2, adding: false }) -> 'Removing 1 file' */
export function withheld(sheet: Sheet): string | null {
  if (sheet.committing) return 'Importing'
  if (sheet.removing > 0) return `Removing ${sheet.removing} ${noun(sheet.removing, 'file')}`
  if (sheet.chosen === 0) return 'Choose files to import'
  if (sheet.read < sheet.chosen) return `Reading ${sheet.read} of ${sheet.chosen}`
  if (sheet.ready === 0) return sheet.adding ? 'Nothing new to add' : 'None of the chosen files could be read.'
  return null
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
