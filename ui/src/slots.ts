import { type Focus, type Move, moved } from './grid'
import type { Renders } from './types'

/* ④ as one slot per image (design spec J3): a slot holds the seed it renders
   at, or null for a random one. A draft's `renders` is the slots read back, so
   the server keeps the one rule and the page draws what the next render draws. */

/** One image's slot: its seed as a decimal string, or null for random. */
export type Slot = string | null

/** Return `renders` as slots, the listed seeds first. e.g. {3, ['144']} -> ['144', null, null] */
export function slots(renders: Renders): Slot[] {
  const random = Math.max(renders.count - renders.seeds.length, 0)
  return [...renders.seeds, ...Array<Slot>(random).fill(null)]
}

/** Return the `renders` `held` reads as. e.g. [null, '144'] -> {2, ['144']} */
export function renders(held: Slot[]): Renders {
  return { count: held.length, seeds: held.filter((one): one is string => one !== null) }
}

/** Return `held` with one more slot, random. */
export function more(held: Slot[]): Slot[] {
  return [...held, null]
}

/** Return `held` less its last random slot, else its last seed; one slot stays. */
export function fewer(held: Slot[]): Slot[] {
  if (held.length <= 1) return held
  const random = held.lastIndexOf(null)
  const at = random >= 0 ? random : held.length - 1
  return held.filter((_, index) => index !== at)
}

/**
 * Return `held` with slot `at` set to `typed`, or the refusal that keeps it.
 *
 * Empty is random. A seed is digits, kept as its decimal without leading zeros as
 * the server reads it, and one already in another slot is refused.
 * e.g. ([null, '144'], 0, '0144') -> 'seed 144 is already in slot 2'
 */
export function set(held: Slot[], at: number, typed: string): Slot[] | string {
  const trimmed = typed.trim()
  if (trimmed === '') return held.map((one, index) => (index === at ? null : one))
  if (!/^\d+$/.test(trimmed)) return `a seed is digits alone, not ${JSON.stringify(trimmed)}`
  const seed = String(BigInt(trimmed))
  const taken = held.findIndex((one, index) => index !== at && one === seed)
  if (taken >= 0) return `seed ${seed} is already in slot ${taken + 1}`
  return held.map((one, index) => (index === at ? seed : one))
}

/** Return the enabled stop of `row` nearest `column`, the left first on a tie; `column` when none is.

    e.g. ([false, true], 0) -> 1, as a disabled `−` passes its focus to `+` */
export function nearest(row: boolean[], column: number): number {
  for (let away = 0; away < row.length; away += 1)
    for (const at of [column - away, column + away]) if (row[at]) return at
  return column
}

/**
 * Return ④'s focus after `move`, and the column a row move keeps (D6).
 *
 * `enabled` holds a row per stop row: the count's `−` `+`, then each slot. A row move
 * keeps the column the focus is in, or from a one-stop row `kept`, the one it last
 * held; a column move onto a disabled stop stays. Each lands on its row's nearest
 * enabled stop. e.g. ([[true, true], [true]], {row 0, column 1}, 'row+', 1)
 * -> {focus {row 1, column 0}, kept 1}
 */
export function stepFour(
  enabled: boolean[][],
  at: Focus,
  move: Move,
  kept: number,
): { focus: Focus; kept: number } {
  const last = enabled.map((one) => one.length - 1)
  if (move.startsWith('column')) {
    const to = moved(last, at, move)
    return enabled[to.row]?.[to.column] ? { focus: to, kept: to.column } : { focus: at, kept }
  }
  const column = (enabled[at.row]?.length ?? 0) > 1 ? at.column : kept
  const to = moved(last, { row: at.row, column }, move)
  return { focus: { row: to.row, column: nearest(enabled[to.row] ?? [], to.column) }, kept: column }
}
