import { type Pairs, complete, held, lone as loneOf } from './pairs'
import type { Mode, Step } from './stages'

/* The Leave dialog as plain functions: the lone point a stage holds, the question leaving it
   asks and the pairs left once the point is dropped. */

/* A stage that holds pairs, and what the dialog says of them. `saved` is when stage 1's pairs
   were last saved, null on any other stage or before the first save. */
export interface Stage {
  mode: Mode
  step: Step
  pairs: Pairs
  saved: Date | null
}

/* The lone point: its 1-based number, the image it lies on and the image that lacks its match. */
export interface Lone {
  number: number
  on: string
  missing: string
}

/* What the dialog shows: the question, the pairs that stand and, for stage 1, when they were saved. */
export interface Ask {
  title: string
  standing: string
  saved: string | null
}

/* The two images a step pairs, the `a` side first, or null for a step with no pairs. */
function imagesOf(mode: Mode, step: Step): readonly [string, string] | null {
  if (step === 'photo') return ['tattoo', 'photograph']
  if (step !== 'render') return null
  return mode === 'direct' ? ['tattoo', 'render'] : ['photograph', 'render']
}

const clock = (at: Date): string =>
  `${String(at.getHours()).padStart(2, '0')}:${String(at.getMinutes()).padStart(2, '0')}`

/** Return the lone point of `stage`, or null when it holds none or pairs no images.
    e.g. point 8 on the tattoo of stage 1 -> { number: 8, on: "tattoo", missing: "photograph" } */
export function lone(stage: Stage): Lone | null {
  const images = imagesOf(stage.mode, stage.step)
  const alone = loneOf(stage.pairs)
  if (images === null || alone === null) return null
  const at = (side: 'a' | 'b'): string => images[side === 'a' ? 0 : 1]
  return { number: alone.index + 1, on: at(alone.has), missing: at(alone.waiting) }
}

/** Return the question leaving `stage` asks, or null when it holds no lone point.
    e.g. point 8 and seven pairs on stage 1 ->
    { title: "Point 8 has no match on the photograph", standing: "7 pairs stand", saved: "saved 14:05" } */
export function asks(stage: Stage): Ask | null {
  const alone = lone(stage)
  if (alone === null) return null
  const count = complete(stage.pairs).length
  const standing = count === 0 ? 'no pair stands' : `${count} ${count === 1 ? 'pair stands' : 'pairs stand'}`
  const saved = stage.step === 'photo' && count > 0 ? (stage.saved ? `saved ${clock(stage.saved)}` : 'saved') : null
  return { title: `Point ${alone.number} has no match on the ${alone.missing}`, standing, saved }
}

/** Return `pairs` without the lone point and with every complete pair kept, as *Leave* does;
    the same state when none is lone. */
export function left(pairs: Pairs): Pairs {
  return loneOf(pairs) === null ? pairs : held(complete(pairs))
}
