import { type Draft, type Rules, blank } from './polygon'
import type { Point, TattooLimits } from './types'

/* The limb and the exclusions of the render stage: one outline that keeps the ink inside it
   and any number that remove it, each a `polygon.ts` draft. One is drawn at a time, and
   while it is the pair editor is held. Every function returns a new state. */

export type Kind = 'limb' | 'exclusion'

/* The outline being drawn: the limb, or the exclusion at `index` of the list. */
export interface Active {
  kind: Kind
  index: number
}

export interface Outlines {
  limb: Draft | null
  exclusions: readonly Draft[]
  active: Active | null
}

export const none: Outlines = { limb: null, exclusions: [], active: null }

/* One line of the list: which outline it is, what it says and whether it is being drawn. */
export interface Row {
  kind: Kind
  index: number
  title: string
  label: string
  drawing: boolean
}

/** Return the rules an outline is drawn by in an image of `size`, the floor from the list's limits. */
export function rulesOf(limits: TattooLimits, size: readonly [number, number]): Rules {
  return { min: limits.region_min, max: limits.outline_max, width: size[0], height: size[1] }
}

/** Return the draft being drawn, or null when none is. */
export function drawing(state: Outlines): Draft | null {
  const { active } = state
  if (!active) return null
  return active.kind === 'limb' ? state.limb : (state.exclusions[active.index] ?? null)
}

/** Return the state with an outline begun: the limb, drawn again if there is one; a new
    exclusion, or, with `index`, that exclusion edited. A new exclusion takes the one
    nobody has drawn on yet rather than a second. */
export function begun(state: Outlines, kind: Kind, index?: number): Outlines {
  if (kind === 'limb') return { ...state, limb: state.limb ?? blank, active: { kind, index: 0 } }
  const empty = state.exclusions.findIndex((one) => one.points.length === 0)
  const at = index ?? empty
  if (at >= 0 && at < state.exclusions.length) return { ...state, active: { kind, index: at } }
  return {
    ...state,
    exclusions: [...state.exclusions, blank],
    active: { kind, index: state.exclusions.length },
  }
}

/** Return the state with `draft` as the outline being drawn; unchanged when none is. */
export function drawn(state: Outlines, draft: Draft): Outlines {
  const { active } = state
  if (!active) return state
  if (active.kind === 'limb') return { ...state, limb: draft }
  return {
    ...state,
    exclusions: state.exclusions.map((one, at) => (at === active.index ? draft : one)),
  }
}

/** Return the state with the drawing ended once the outline being drawn is closed; else unchanged. */
export function closed(state: Outlines): Outlines {
  return drawing(state)?.closed ? { ...state, active: null } : state
}

/** Return the state with the drawing ended, the outline left as it stands, open or closed. */
export function stopped(state: Outlines): Outlines {
  return state.active === null ? state : { ...state, active: null }
}

/* An outline as a panel draws it. */
export interface Shape {
  kind: Kind
  points: readonly Point[]
  closed: boolean
  drawing: boolean
}

/** Return each outline with a point, the limb first, for a panel to draw. */
export function shapes(state: Outlines): Shape[] {
  return rows(state).flatMap(({ kind, index, drawing: on }) => {
    const draft = kind === 'limb' ? state.limb : state.exclusions[index]
    return draft ? [{ kind, points: draft.points, closed: draft.closed, drawing: on }] : []
  })
}

const points = (count: number): string => `${count} point${count === 1 ? '' : 's'}`

/** Return the list's rows, the limb first.
    e.g. a closed limb of 9 points -> "9 points · keeps"; one being drawn -> "drawing · 3 points" */
export function rows(state: Outlines): Row[] {
  const listed: Row[] = []
  const one = (kind: Kind, index: number, draft: Draft): void => {
    const on = state.active?.kind === kind && state.active.index === index
    if (draft.points.length === 0 && !on) return
    const does = kind === 'limb' ? 'keeps' : 'removes'
    const count = points(draft.points.length)
    const label = on ? `drawing · ${count}` : draft.closed ? `${count} · ${does}` : `open · ${count}`
    listed.push({
      kind,
      index,
      title: kind === 'limb' ? 'limb' : `exclusion ${index + 1}`,
      label,
      drawing: on,
    })
  }
  if (state.limb) one('limb', 0, state.limb)
  state.exclusions.forEach((draft, index) => one('exclusion', index, draft))
  return listed
}

/** Tell whether the pair editor is held: an outline is being drawn. */
export function held(state: Outlines): boolean {
  return state.active !== null
}

/** Return what a preview or a bake is sent: the closed limb, or null, and each closed exclusion. */
export function regions(state: Outlines): { limb: Point[] | null; exclusions: Point[][] } {
  const copy = (draft: Draft): Point[] => draft.points.map(([x, y]): Point => [x, y])
  return {
    limb: state.limb?.closed ? copy(state.limb) : null,
    exclusions: state.exclusions.filter((draft) => draft.closed).map(copy),
  }
}
