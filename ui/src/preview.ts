/* The preview's schedule and its answers, as plain functions. A change asks for a preview a
   declared time after the last one; of the asks made, the newest answer alone is kept, the
   last one stays drawn at half opacity while the next is asked, and a refusal clears it. */

export interface Answer {
  /* The object URL of the JPEG, and its crop in the target's pixels. */
  url: string
  box: { x: number; y: number; width: number; height: number }
  white: number
}

export interface Previewing {
  /* The number of the newest ask, 0 before any. */
  newest: number
  /* The newest ask has no answer yet. */
  asking: boolean
  /* What is drawn: the newest answer, or while the next is asked, the one before. */
  shown: Answer | null
  /* The words of the newest ask's refusal. */
  refusal: string | null
}

export const idle: Previewing = { newest: 0, asking: false, shown: null, refusal: null }

/** Tell whether a preview may be asked: at least `floor` complete pairs stand. */
export function previewable(complete: number, floor: number): boolean {
  return complete >= floor
}

/** Tell whether the ask for the change at `last` is due at `now`, `wait` ms after it.
    `last` is null once the change was asked. e.g. last 600, wait 1000 -> due from 1600 */
export function due(last: number | null, now: number, wait: number): boolean {
  return last !== null && now - last >= wait
}

/** Return the state after an ask is made, and the ask's number. The drawn answer stays. */
export function asked(state: Previewing): { state: Previewing; ask: number } {
  const ask = state.newest + 1
  return { state: { ...state, newest: ask, asking: true, refusal: null }, ask }
}

/** Return the state after ask `ask` is answered; an older ask's answer is dropped. */
export function answered(state: Previewing, ask: number, answer: Answer): Previewing {
  if (ask !== state.newest) return state
  return { ...state, asking: false, shown: answer, refusal: null }
}

/** Return the state after ask `ask` is refused, with no answer drawn; an older ask's refusal
    is dropped. */
export function refused(state: Previewing, ask: number, reason: string): Previewing {
  if (ask !== state.newest) return state
  return { ...state, asking: false, shown: null, refusal: reason }
}

/** Tell whether the drawn answer is at half opacity: another is being asked. */
export function dimmed(state: Previewing): boolean {
  return state.asking && state.shown !== null
}

/** Return the opacity the drawn answer takes, the operator's, halved while dimmed. */
export function opacityOf(state: Previewing, chosen: number): number {
  return dimmed(state) ? chosen / 2 : chosen
}
