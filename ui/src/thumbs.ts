import { photoUrl, sourceThumbAt } from './api'
import { moved, type Move } from './grid'
import type { QuotedCollection, QuoteSource } from './types'

/* The Render dialog's thumbnails (design spec J4·1): per flow the photographs that
   render, less those taken out, capped as Review's head is. */

/** How many thumbnails a row shows, before `+n`. */
export const ROW_THUMBS = 15

/** Why Render is off once every photograph of every row is taken out. */
export const NOTHING_LEFT = 'Nothing left to render.'

/** One photograph drawn as a thumbnail; `fallback` is the run's own, for a run not
    among the hub's sources, and `times` its images when above one. */
export interface Thumb {
  key: string
  run: string
  src: string
  fallback: string
  title: string
  times: number | null
}

type Flows = QuotedCollection['flows'][number]

const keyOf = (collection: string, flow: string, source: QuoteSource) =>
  `${collection}|${source.digest}|${flow}`

function thumb(collection: string, flow: string, source: QuoteSource, images: number): Thumb {
  const { name, digest, run, version } = source
  return {
    key: keyOf(collection, flow, source),
    run,
    src: sourceThumbAt(collection, name),
    fallback: photoUrl({ collection, digest, flow }),
    title: version === null ? name : `${name} v${version}`,
    times: images > 1 ? images : null,
  }
}

/** Return a flow's first `ROW_THUMBS` thumbnails, less each key in `out`, and how many
    past them. */
export function thumbs(
  collection: string,
  flow: string,
  sources: Flows['sources'],
  out: ReadonlySet<string> = new Set(),
): { thumbs: Thumb[]; more: number } {
  const all = sources
    .filter((one) => !out.has(keyOf(collection, flow, one)))
    .map((one) => thumb(collection, flow, one, one.images))
  return { thumbs: all.slice(0, ROW_THUMBS), more: Math.max(all.length - ROW_THUMBS, 0) }
}

/** Return whether `row` has a photograph and each is taken out, its key in `out`. */
export function allOut(row: QuotedCollection, out: ReadonlySet<string>): boolean {
  const keys = row.flows.flatMap((one) =>
    one.sources.map((source) => keyOf(row.collection, one.flow, source)),
  )
  return keys.length > 0 && keys.every((key) => out.has(key))
}

/** Return why Render is off: `NOTHING_LEFT` once each of `rows` is all out, else `disabled`. */
export function confirmReason(
  rows: QuotedCollection[],
  out: ReadonlySet<string>,
  disabled: string | null,
): string | null {
  return rows.length > 0 && rows.every((row) => allOut(row, out)) ? NOTHING_LEFT : disabled
}

/** Return the tile index after `move`, across flows of `sizes` tiles in order, each above 0;
    a flow is a grid row. e.g. sizes [3, 2], index 2, 'row+' -> 4 */
export function tileMoved(sizes: number[], index: number, move: Move): number {
  let row = 0
  let column = index
  while (row < sizes.length - 1 && column >= (sizes[row] ?? 0)) column -= sizes[row++] ?? 0
  const at = moved(sizes.map((size) => size - 1), { row, column }, move)
  return sizes.slice(0, at.row).reduce((sum, size) => sum + size, 0) + at.column
}
