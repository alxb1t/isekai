import type { Pairs } from './pairs'
import type { Mode } from './stages'
import type { Outline, Pair, Point } from './types'

/* The state of stage 2's ask for proposed pairs, as plain functions over a record keyed by
   a tattoo and a render. A key with no entry has not been asked; an entry is never removed
   by an answer, so a stage asks once. */

export type Ask =
  | { state: 'asking' }
  | { state: 'answered'; count: number }
  | { state: 'refused' }

export type Asks = Readonly<Record<string, Ask>>

export const noAsks: Asks = {}

/** Return the key of the ask for `tattoo` on the render `version` and `seed`.
    e.g. "bow", "v2", "7" -> '["bow","v2","7"]' */
export const keyOf = (tattoo: string, version: string, seed: string): string =>
  JSON.stringify([tattoo, version, seed])

/** Return whether stage 2 asks now: a two-stage tattoo or a cut, no pair held, and no ask
    recorded under `key`, with `points` to send and no read of the tattoo in flight (`reading`).
    The direct stage has no photograph to read a pose from. */
export function due(
  mode: Mode | null,
  pairs: Pairs,
  asks: Asks,
  key: string,
  points: number,
  reading: boolean,
): boolean {
  if (mode !== 'two-stage' && mode !== 'cut') return false
  if (reading || points === 0) return false
  return pairs.slots.length === 0 && !(key in asks)
}

/** Return `asks` with `key` asked and not yet answered. */
export const asked = (asks: Asks, key: string): Asks => ({ ...asks, [key]: { state: 'asking' } })

/** Return whether `ask`, as `asked` recorded it under `key`, is still the entry held there:
    a later ask or an answer replaces it, so its own response no longer applies.
    e.g. the entry of the first ask, after a second ask under the same key -> false */
export const stands = (asks: Asks, key: string, ask: Ask | undefined): boolean =>
  ask !== undefined && asks[key] === ask

/** Return `asks` with `key` answered by `count` pairs. */
export const answered = (asks: Asks, key: string, count: number): Asks => ({
  ...asks,
  [key]: { state: 'answered', count },
})

/** Return `asks` with `key` refused. */
export const refused = (asks: Asks, key: string): Asks => ({
  ...asks,
  [key]: { state: 'refused' },
})

/** Return the line stage 2 shows for `key`, or null when there is nothing to say.
    e.g. asked -> "Proposing pairs…"; answered with no pair -> "Nothing proposed — place the pairs by clicking" */
export function view(asks: Asks, key: string): string | null {
  const ask = asks[key]
  if (ask === undefined) return null
  if (ask.state === 'asking') return 'Proposing pairs…'
  if (ask.state === 'refused') return 'Could not propose pairs — place them by clicking'
  return ask.count === 0 ? 'Nothing proposed — place the pairs by clicking' : null
}

/** Return the tattoo's points on the photograph: the photograph side of the stage-1 pairs of
    a two-stage tattoo, a cut's outline, and none for the direct stage.
    e.g. the pair [[10, 20], [300, 400]] of a two-stage tattoo -> [[300, 400]] */
export function pointsOf(mode: Mode, stage1: readonly Pair[], outline: Outline): Point[] {
  if (mode === 'cut') return outline.points.map(([x, y]): Point => [x, y])
  if (mode === 'two-stage') return stage1.map(([, photograph]): Point => [photograph[0], photograph[1]])
  return []
}
