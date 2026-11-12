import type { Point } from './types'

/* An outline being drawn: its vertices, whether it is closed, and what to undo.
   Every function returns a new state and leaves its argument as it was. */
interface Shape {
  points: readonly Point[]
  closed: boolean
}

export interface Draft extends Shape {
  past: readonly Shape[]
}

/* What an outline is held to: its least and most vertices, and the image it lies in. */
export interface Rules {
  min: number
  max: number
  width: number
  height: number
}

/* The closing and picking radius, in screen pixels: at every zoom it is the same on screen. */
export const RADIUS = 10

export const blank: Draft = { points: [], closed: false, past: [] }

/** Return a draft holding `points`, with nothing to undo. */
export function drafted(points: readonly Point[], closed: boolean): Draft {
  return { points: points.map(([x, y]): Point => [x, y]), closed, past: [] }
}

function changed(draft: Draft, next: Shape): Draft {
  const { points, closed } = draft
  return { ...next, past: [...draft.past, { points, closed }] }
}

function inside(at: Point, rules: Rules): boolean {
  return at[0] >= 0 && at[0] <= rules.width && at[1] >= 0 && at[1] <= rules.height
}

function held(at: Point, rules: Rules): Point {
  return [Math.min(rules.width, Math.max(0, at[0])), Math.min(rules.height, Math.max(0, at[1]))]
}

/** Return the draft with a vertex at `at`; unchanged when closed, full or off the image. */
export function added(draft: Draft, at: Point, rules: Rules): Draft {
  if (draft.closed || draft.points.length >= rules.max || !inside(at, rules)) return draft
  return changed(draft, { points: [...draft.points, at], closed: false })
}

/** Tell whether a click at `at` closes an open outline: it has the floor's vertices and
    lies within `RADIUS` screen pixels of the first, at `scale`. */
export function closes(draft: Draft, at: Point, scale: number, rules: Rules): boolean {
  if (draft.closed || draft.points.length < rules.min) return false
  return distance(draft.points[0], at) * scale <= RADIUS
}

/** Return the draft closed; unchanged when it holds fewer vertices than the floor. */
export function closed(draft: Draft, rules: Rules): Draft {
  if (draft.closed || draft.points.length < rules.min) return draft
  return changed(draft, { points: draft.points, closed: true })
}

/** Return the index of the vertex within `RADIUS` screen pixels of `at`, the nearest, else null. */
export function vertexAt(draft: Draft, at: Point, scale: number): number | null {
  let found: number | null = null
  let least = RADIUS / scale
  draft.points.forEach((point, index) => {
    const gap = distance(point, at)
    if (gap <= least) {
      least = gap
      found = index
    }
  })
  return found
}

/** Return the draft with vertex `index` at `to`, held to the image. A drag is one change:
    pass `fresh` false for each move after its first. */
export function moved(draft: Draft, index: number, to: Point, rules: Rules, fresh = true): Draft {
  if (index < 0 || index >= draft.points.length) return draft
  const points = draft.points.map((point, at): Point => (at === index ? held(to, rules) : point))
  const next = { points, closed: draft.closed }
  return fresh ? changed(draft, next) : { ...next, past: draft.past }
}

/** Return the draft with a vertex on the edge nearest `at`, after the edge's first end.
    e.g. a click beside the edge (0,0)-(10,0) at (4,3) -> a vertex at (4,0) */
export function inserted(draft: Draft, at: Point, rules: Rules): Draft {
  const { points } = draft
  if (points.length < 2 || points.length >= rules.max) return draft
  const edges = draft.closed ? points.length : points.length - 1
  let best = { gap: Infinity, after: 0, on: points[0] }
  for (let after = 0; after < edges; after++) {
    const on = nearestOn(points[after], points[(after + 1) % points.length], at)
    const gap = distance(on, at)
    if (gap < best.gap) best = { gap, after, on }
  }
  const next = [...points.slice(0, best.after + 1), best.on, ...points.slice(best.after + 1)]
  return changed(draft, { points: next, closed: draft.closed })
}

/** Return the draft without vertex `index`; a closed outline left under the floor opens. */
export function removed(draft: Draft, index: number, rules: Rules): Draft {
  if (index < 0 || index >= draft.points.length) return draft
  const points = draft.points.filter((_, at) => at !== index)
  return changed(draft, { points, closed: draft.closed && points.length >= rules.min })
}

/** Return the draft with no vertex and open, as a change that can be undone. */
export function cleared(draft: Draft): Draft {
  return draft.points.length === 0 && !draft.closed ? draft : changed(draft, { points: [], closed: false })
}

/** Return the draft as it was before its last change; unchanged with nothing to undo. */
export function undone(draft: Draft): Draft {
  const last = draft.past[draft.past.length - 1]
  if (!last) return draft
  return { points: last.points, closed: last.closed, past: draft.past.slice(0, -1) }
}

/** Return the vertices' bounding box, or null with none. e.g. (2,3) and (10,9) -> 2,3 8x6 */
export function box(draft: Draft): { x: number; y: number; width: number; height: number } | null {
  if (draft.points.length === 0) return null
  const xs = draft.points.map(([x]) => x)
  const ys = draft.points.map(([, y]) => y)
  const [x, y] = [Math.min(...xs), Math.min(...ys)]
  return { x, y, width: Math.max(...xs) - x, height: Math.max(...ys) - y }
}

/** Tell whether the outline is closed and holds the floor's vertices, at most the ceiling. */
export function ready(draft: Draft, rules: Rules): boolean {
  return draft.closed && draft.points.length >= rules.min && draft.points.length <= rules.max
}

function distance(a: Point, b: Point): number {
  return Math.hypot(a[0] - b[0], a[1] - b[1])
}

function nearestOn(from: Point, to: Point, at: Point): Point {
  const [dx, dy] = [to[0] - from[0], to[1] - from[1]]
  const length = dx * dx + dy * dy
  const t = length === 0 ? 0 : Math.min(1, Math.max(0, ((at[0] - from[0]) * dx + (at[1] - from[1]) * dy) / length))
  return [from[0] + t * dx, from[1] + t * dy]
}
