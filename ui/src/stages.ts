import type { Stage1, Tattoo, TattooLimits } from './types'

/* The stages of the placement screen, as plain functions: the mode a tattoo takes, the steps
   of that mode, where the outline step goes forward, the step a card opens and the step a
   mode takes in place of one it skips. A number names one screen in every mode. */

export type Mode = 'cut' | 'direct' | 'two-stage'
export type Step = 'tattoo' | 'outline' | 'photo' | 'render'

export interface StepInfo {
  step: Step
  /* The step's number: 1 to 4, kept in every mode, so a step a mode skips is absent. */
  number: number
  label: string
}

const CIRCLED = ['⓪', '①', '②', '③', '④', '⑤']

/** Return the circled digit of a step's number. e.g. 3 -> "③" */
export function circled(number: number): string {
  return CIRCLED[number] ?? String(number)
}

/** Return how a tattoo is placed: a cut, directly on the render, or in two stages.
    e.g. an upload flagged *not on this photo* -> "direct" */
export function modeOf(kind: Tattoo['kind'], notOnPhoto: boolean): Mode {
  if (kind === 'cut') return 'cut'
  return notOnPhoto ? 'direct' : 'two-stage'
}

/** Return the steps of `mode`, each with the number it keeps.
    e.g. a cut -> tattoo ①, outline ②, photograph ↔ render ④ */
export function stepsOf(mode: Mode): StepInfo[] {
  const first: StepInfo[] = [
    { step: 'tattoo', number: 1, label: 'tattoo' },
    { step: 'outline', number: 2, label: 'outline' },
  ]
  if (mode === 'two-stage') {
    return [
      ...first,
      { step: 'photo', number: 3, label: 'tattoo ↔ photograph' },
      { step: 'render', number: 4, label: 'photograph ↔ render' },
    ]
  }
  if (mode === 'direct') return [...first, { step: 'render', number: 3, label: 'tattoo ↔ render' }]
  return [...first, { step: 'render', number: 4, label: 'photograph ↔ render' }]
}

/* Where the outline step goes forward: to a step, or waiting with its reason. */
export interface Forward {
  step: Step | null
  wait: string | null
}

/** Return where the outline step goes forward, once its outline is closed: stage 1 for an
    upload, the direct stage or stage 2 for a cut; while it is open it waits.
    e.g. open with 27 points -> waits "outline open · 27 points" */
export function forwardOf(mode: Mode, outline: { closed: boolean; points: number }): Forward {
  if (!outline.closed) {
    const points = outline.points === 1 ? '1 point' : `${outline.points} points`
    return { step: null, wait: `outline open · ${points}` }
  }
  return { step: mode === 'two-stage' ? 'photo' : 'render', wait: null }
}

/** Return the step a card opens: the outline until the tattoo is outlined, then stage 1 for
    a two-stage tattoo short of `floor` stage-1 pairs, else the render stage. */
export function startStep(tattoo: Tattoo, state: Stage1 | undefined, floor: number): Step {
  if (!tattoo.outlined) return 'outline'
  const mode = modeOf(tattoo.kind, state?.not_on_photo ?? false)
  return mode === 'two-stage' && (state?.pairs.length ?? 0) < floor ? 'photo' : 'render'
}

/** Return the step `mode` takes in place of `step`: the render stage for the photograph
    stage of a mode that has none, else `step` itself. e.g. a cut asked `photo` -> "render" */
export function skipped(mode: Mode, step: Step): Step {
  return step === 'photo' && mode !== 'two-stage' ? 'render' : step
}

/** Return the pairs a stage goes forward with: stage 1's floor on the photograph, else the
    direct stage's for a direct tattoo and stage 2's for the others. */
export function floorOf(mode: Mode, step: Step, limits: TattooLimits): number {
  if (step === 'photo') return limits.floor_stage1
  return mode === 'direct' ? limits.floor_direct : limits.floor_stage2
}
