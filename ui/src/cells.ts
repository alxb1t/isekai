import { type Focus, type Move, moved } from './grid'
import type { HubCell, ImageRef, RenderDetail } from './types'

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
      return { action: 'tick', hint: null }
    case 'tagged':
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

/** The pick of a source's images (D2): the photograph's row, then a row per flow. */
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

/** Return the pick's head, naming the image compare started from and the focused tile.

    e.g. summon v3·7, focus on summon v2·7 -> "Compare summon v3 · seed 7 with summon v2 · seed 7…" */
export function pickHead(from: { flow: string; version: number; seed: string }, tile: PickTile): string {
  const named = (one: NonNullable<PickTile>) => `${one.flow} v${one.version} · seed ${one.seed}`
  return `Compare ${named(from)} with ${tile === null ? 'photograph' : named(tile)}…`
}

/** Return the pick's focus after `move`: a row move keeps the column, held at a
    shorter row's end. */
export const movePick = (grid: SourceGrid, at: Focus, move: Move): Focus =>
  moved(
    grid.rows.map((one) => one.tiles.length - 1),
    at,
    move,
  )
