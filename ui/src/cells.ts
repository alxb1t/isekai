import { type Focus, type Move, moved } from './grid'
import type { HubCell, ImageRef, RenderDetail } from './types'
import { noun } from './words'

/** Return an image as a selection holds it. e.g. "0d4b…|summon-anime-wai|1|42" */
export function imageKey(one: ImageRef): string {
  return `${one.digest}|${one.flow}|${one.version}|${one.seed}`
}

/** Return an image's name as a heading shows it, or the photograph's for null.

    e.g. {flow: 'summon-anime-wai', version: 2, seed: '7'} -> "summon-anime-wai · v2 · seed 7" */
export const imageName = (one: { flow: string; version: number; seed: string } | null): string =>
  one === null ? 'photograph' : `${one.flow} · v${one.version} · seed ${one.seed}`

/* What a click or ↵ on a hub cell does follows its stage, as the design spec's J2
   states: one table, so no template decides it on its own. */
export type Action = 'tick' | 'review' | 'sheet' | 'view' | 'none'

/** A cell whose run holds no directory for the flow, or a source with no run. */
export const EMPTY_CELL: Readonly<HubCell> = {
  stage: null,
  renders: 0,
  refusal: null,
  status: null,
  newest: null,
  short: null,
  images: [],
}

export interface CellAction {
  action: Action
  hint: string | null
}

/** Return what a click on `cell` does, and the hint its focus shows. */
export function action(cell: HubCell): CellAction {
  switch (cell.stage) {
    case null:
    case 'assigned':
    case 'tagged':
      return { action: 'tick', hint: null }
    case 'unreadable':
      return { action: 'none', hint: null }
    case 'sheet':
    case 'draft':
      return { action: 'review', hint: '↵ review' }
    case 'approved':
    case 'rendered':
      return cell.newest === null
        ? { action: 'sheet', hint: '↵ review' }
        : { action: 'view', hint: '↵ view' }
  }
}

/** Return the ready tile's words while `cell`'s newest approval lacks images, else null.

    e.g. short 2 -> "ready · 2 images" */
export function ready(cell: HubCell): string | null {
  return cell.short !== null && cell.short > 0
    ? `ready · ${cell.short} ${noun(cell.short, 'image')}`
    : null
}

/* Seeds are decimal strings past a number's safe range: a shorter one is smaller. */
const bySeed = (a: string, b: string): number =>
  a.length - b.length || (a < b ? -1 : a > b ? 1 : 0)

/** Return a cell's images by version, then by seed as a number.

    e.g. [v2·4, v1·9, v1·2] -> [v1·2, v1·9, v2·4] */
export function cellOrder<T extends { version: number; seed: string }>(images: readonly T[]): T[] {
  return [...images].sort((a, b) => a.version - b.version || bySeed(a.seed, b.seed))
}

/** Return whether `cell` is waiting for Prepare: assigned, or tagged with no sheet yet. */
export function pending(cell: HubCell): boolean {
  return cell.stage === 'assigned' || cell.stage === 'tagged'
}

/** Return whether `cell`'s tick stays: a stage past pending holds work. */
export function locked(cell: HubCell): boolean {
  return cell.stage !== null && !pending(cell)
}

/** Return the rows a tick lands on: a click's own row; space's, the selection's.

    A pointer lands on one cell, so a click ticks that cell whatever rows ⇧↑↓
    selected; space ticks the focused column for every selected row. */
export function targets(selected: ReadonlySet<number>, row: number, pointer: boolean): number[] {
  return pointer || selected.size === 0 ? [row] : [...selected]
}

/** Return whether a click on a cell runs its action.

    A click inside the cell's refusal, or one that ends a text selection, is
    reading or copying the fix, never a tick. */
export function clicks(
  target: { closest(selector: string): unknown } | null,
  selection: string,
): boolean {
  return selection === '' && !target?.closest('.hub__refusal')
}

/** A tile of the pick: an image of a flow, or null for the photograph. */
export type PickTile = { flow: string; version: number; seed: string } | null

/** The pick of a source's images: the photograph's row, then a row per flow holding images. */
export interface SourceGrid {
  rows: { flow: string | null; tiles: PickTile[] }[]
  /* The image compare started from, marked. */
  origin: Focus
  /* Where the focus opens. */
  start: Focus
}

/** Return the pick of `detail`'s source, focused on its seed's newest older
    version, else the image before it in its row, else the photograph.

    e.g. summon [v1·7, v2·7] from v2·7, compare 1 -> start {row 1, column 0} */
export function sourceGrid(detail: RenderDetail): SourceGrid {
  const rows: SourceGrid['rows'] = [
    { flow: null, tiles: [null] },
    ...detail.source.map(({ flow, images }) => ({
      flow,
      tiles: images.map((one) => ({ flow, ...one })),
    })),
  ]
  const row = rows.findIndex((one) => one.flow === detail.flow)
  const at = (version: number | null) =>
    (rows[row]?.tiles ?? []).findIndex(
      (one) => one !== null && one.version === version && one.seed === detail.seed,
    )
  const origin = { row, column: at(detail.version) }
  const paired = at(detail.compare)
  const start =
    paired >= 0
      ? { row, column: paired }
      : origin.column > 0
        ? { row, column: origin.column - 1 }
        : { row: 0, column: 0 }
  return { rows, origin, start }
}

/** Return a pick tile's caption: its version alone, so a long seed never widens the grid. */
export const tileCaption = (tile: PickTile): string =>
  tile === null ? 'photograph' : `v${tile.version}`

/** Return the pick's head as its two lines, the image compare started from and the focused tile.

    e.g. summon v3·7, focus on summon v2·7 -> ["Compare summon v3 · seed 7", "with summon v2 · seed 7"] */
export function pickHead(
  from: { flow: string; version: number; seed: string },
  tile: PickTile,
): [string, string] {
  const named = (one: NonNullable<PickTile>) => `${one.flow} v${one.version} · seed ${one.seed}`
  return [`Compare ${named(from)}`, `with ${tile === null ? 'photograph' : named(tile)}`]
}

/** The cell modal's grid: a cell's images in one order, cut into balanced rows. */
export interface CellGrid {
  rows: { tiles: NonNullable<PickTile>[] }[]
  /* The seeds rendered under more than one version, each marked ⇄. */
  shared: ReadonlySet<string>
  /* Where the focus opens. */
  start: Focus
}

/** Return how many tiles a row of the cell modal holds: at most three, the rows balanced.

    e.g. 4 -> 2, 5 -> 3, 7 -> 3, 0 -> 0 */
export function gridColumns(count: number): number {
  return count === 0 ? 0 : Math.ceil(count / Math.ceil(count / 3))
}

/** Return the cell modal's grid of `flow`'s `images`, focused on `at`.

    e.g. v1 [7, 2], v2 [7] at v1·7 -> rows [v1·2, v1·7, v2·7], shared {7}, start {row 0, column 1} */
export function cellGrid(
  flow: string,
  images: readonly { version: number; seed: string }[],
  at: { version: number; seed: string },
): CellGrid {
  const tiles = cellOrder(images).map((one) => ({ flow, ...one }))
  const columns = gridColumns(tiles.length)
  const rows: CellGrid['rows'] = []
  for (let from = 0; from < tiles.length; from += columns)
    rows.push({ tiles: tiles.slice(from, from + columns) })
  const versions = new Map<string, number>()
  for (const { seed } of tiles) versions.set(seed, (versions.get(seed) ?? 0) + 1)
  const shared = new Set([...versions].filter(([, count]) => count > 1).map(([seed]) => seed))
  const index = tiles.findIndex((one) => one.version === at.version && one.seed === at.seed)
  const start =
    index < 0
      ? { row: 0, column: 0 }
      : { row: Math.floor(index / columns), column: index % columns }
  return { rows, shared, start }
}

/** Return the cell modal's focus after `move`: `l` at a row's end goes on to the
    next row's first, `h` at a row's start back to the previous row's last; a row
    move keeps the column, held at a shorter row's last tile.

    e.g. rows [3, 2], {row 0, column 2}: 'column+' -> {row 1, column 0} */
export function moveCell(grid: CellGrid, at: Focus, move: Move): Focus {
  const last = grid.rows.map((one) => one.tiles.length - 1)
  if (move === 'column+' && at.column === last[at.row] && at.row + 1 < last.length)
    return { row: at.row + 1, column: 0 }
  if (move === 'column-' && at.column === 0 && at.row > 0)
    return { row: at.row - 1, column: last[at.row - 1] }
  return moved(last, at, move)
}

/** Return the pick's focus after `move`: a row move keeps the column, held at a
    shorter row's end. */
export const movePick = (
  grid: { rows: { tiles: readonly unknown[] }[] },
  at: Focus,
  move: Move,
): Focus =>
  moved(
    grid.rows.map((one) => one.tiles.length - 1),
    at,
    move,
  )

/** Return the images a large view walks, wherever it was opened: the photograph's
    row, its flows in the hub's column order, each version oldest first, seeds as numbers.

    e.g. summon [v1·7, v2·7], flat [v1·5] -> summon v1·7, summon v2·7, flat v1·5 */
export function rowOrder(detail: RenderDetail): NonNullable<PickTile>[] {
  return detail.source.flatMap(({ flow, images }) => images.map((one) => ({ flow, ...one })))
}

/** Return where `at` stands in `order`, or -1. */
export const placeOf = (order: NonNullable<PickTile>[], at: NonNullable<PickTile>): number =>
  order.findIndex(
    (one) => one.flow === at.flow && one.version === at.version && one.seed === at.seed,
  )

/** Return the image `by` steps from `at` in `order`, or null, held, at either end. */
export function stepped(
  order: NonNullable<PickTile>[],
  at: NonNullable<PickTile>,
  by: -1 | 1,
): NonNullable<PickTile> | null {
  const index = placeOf(order, at)
  return index < 0 ? null : (order[index + by] ?? null)
}
