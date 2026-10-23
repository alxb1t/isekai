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
 * Empty is random. A seed is digits, and one already in another slot is refused.
 * e.g. ([null, '144'], 0, '144') -> 'seed 144 is already in slot 2'
 */
export function set(held: Slot[], at: number, typed: string): Slot[] | string {
  const seed = typed.trim()
  if (seed === '') return held.map((one, index) => (index === at ? null : one))
  if (!/^\d+$/.test(seed)) return `a seed is digits alone, not ${JSON.stringify(seed)}`
  const taken = held.findIndex((one, index) => index !== at && one === seed)
  if (taken >= 0) return `seed ${seed} is already in slot ${taken + 1}`
  return held.map((one, index) => (index === at ? seed : one))
}
