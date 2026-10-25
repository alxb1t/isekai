/* What a render session's record says, read the one way the list and the page
   both read it. */

import type { Focus } from './grid'
import type { SessionImage, SessionRecord } from './types'

/* Seconds from `started` to `ended`, or to `now` while it runs; null once ended
   outright. e.g. ("…09:12:00Z", "…09:20:00Z") -> 480 */
export function lasted(
  started: string,
  ended: string | null | undefined,
  running: boolean,
  now: number,
): number | null {
  if (ended) return (Date.parse(ended) - Date.parse(started)) / 1000
  return running ? (now - Date.parse(started)) / 1000 : null
}

/* How many images the session was asked to render, across its flows. */
export function asked(record: SessionRecord): number {
  return Object.values(record.asked).reduce((sum, n) => sum + n, 0)
}

/* The word for how a session ended; a record still reading running whose lifetime
   lock no process holds was ended outright. */
export function outcome(record: SessionRecord): string {
  return record.outcome ?? 'ended, no outcome'
}

/** One cell of the session grid: a flow's landed images of one photograph, and how many are to come. */
export interface Cell {
  images: SessionImage[]
  waiting: number
}

/** The session page's grid: a column per photograph, a row per flow, `cells[row][column]`.

    The photographs' row is drawn below the flows' rows, as row `flows.length`. */
export interface Grid {
  digests: string[]
  flows: string[]
  cells: Cell[][]
}

/* Each distinct value of `values`, in the order it first appears. */
const distinct = (values: string[]) => [...new Set(values)]

/** Return a record's grid: what it plans, then any landed image it did not plan.

    A record written before plans were recorded places its landed images, and no
    waiting tile. e.g. planned [{d1, summon, 2}], one landed -> one cell, waiting 1 */
export function grid(record: SessionRecord): Grid {
  const planned = record.planned ?? []
  const digests = distinct([...planned, ...record.images].map((one) => one.digest))
  const flows = distinct([...planned, ...record.images].map((one) => one.flow))
  const at = (one: { flow: string; digest: string }) => `${one.flow}|${one.digest}`
  const landed = new Map<string, SessionImage[]>()
  for (const one of record.images) landed.set(at(one), [...(landed.get(at(one)) ?? []), one])
  const plans = new Map(planned.map((one) => [at(one), one.images]))
  const cells = flows.map((flow) =>
    digests.map((digest) => {
      const images = landed.get(at({ flow, digest })) ?? []
      return { images, waiting: Math.max((plans.get(at({ flow, digest })) ?? 0) - images.length, 0) }
    }),
  )
  return { digests, flows, cells }
}

/** Return the focus on the grid's first landed image, else on its first cell. */
export function first(held: Grid, record: SessionRecord): Focus {
  const landed = record.images[0]
  if (!landed) return { row: 0, column: 0 }
  return { row: held.flows.indexOf(landed.flow), column: held.digests.indexOf(landed.digest) }
}

/** Return each row's last column, the photographs' row the last row, for `moved`.

    e.g. two photographs over one flow -> [1, 1]; no photograph -> [] */
export function lastColumns(held: Grid): number[] {
  if (held.digests.length === 0) return []
  return Array<number>(held.flows.length + 1).fill(held.digests.length - 1)
}
