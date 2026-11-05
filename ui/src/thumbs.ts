import { photoUrl, sourceThumbAt } from './api'
import type { QuotedCollection, QuoteSource } from './types'

/* The Render dialog's thumbnails (design spec J4·1): per flow the photographs that
   render, and the left out by reason and flow, each capped as Review's head is. */

/** How many thumbnails a row shows, before `+n`. */
export const ROW_THUMBS = 15

/** One photograph drawn as a thumbnail; `fallback` is the run's own, for a run not
    among the hub's sources, and `times` its images when above one. */
export interface Thumb {
  key: string
  src: string
  fallback: string
  title: string
  times: number | null
}

type Flows = QuotedCollection['flows'][number]
type Left = QuotedCollection['left_out'][number]

function thumb(collection: string, flow: string, source: QuoteSource, images: number): Thumb {
  const { name, digest, version } = source
  return {
    key: `${collection}|${digest}|${flow}`,
    src: sourceThumbAt(collection, name),
    fallback: photoUrl({ collection, digest, flow }),
    title: version === null ? name : `${name} v${version}`,
    times: images > 1 ? images : null,
  }
}

function capped(all: Thumb[]): { thumbs: Thumb[]; more: number } {
  return { thumbs: all.slice(0, ROW_THUMBS), more: Math.max(all.length - ROW_THUMBS, 0) }
}

/** Return a flow's first `ROW_THUMBS` thumbnails, and how many past them. */
export function thumbs(
  collection: string,
  flow: string,
  sources: Flows['sources'],
): { thumbs: Thumb[]; more: number } {
  return capped(sources.map((one) => thumb(collection, flow, one, one.images)))
}

/** Return the left out grouped by reason and flow, in the order each pair first
    appears, each group capped as a flow's thumbnails are.
    e.g. [a·draft·s, b·new·s, c·draft·s] -> [draft·s: a c, new·s: b] */
export function leftOut(
  collection: string,
  left: Left[],
): { reason: string; flow: string; thumbs: Thumb[]; more: number }[] {
  const groups = new Map<string, { reason: string; flow: string; all: Thumb[] }>()
  for (const one of left) {
    const at = `${one.reason}|${one.flow}`
    const group = groups.get(at) ?? { reason: one.reason, flow: one.flow, all: [] }
    group.all.push(thumb(collection, one.flow, one, 0))
    groups.set(at, group)
  }
  return [...groups.values()].map(({ reason, flow, all }) => ({ reason, flow, ...capped(all) }))
}
