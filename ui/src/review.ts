import { type Pairs, forward } from './pairs'
import type { Mode } from './stages'
import { defaultTone, differs, greyOf } from './tattoos'
import type { Outline, Pair, Point, Preview, Tattoo, TattooLimits } from './types'

/* The review step as plain functions: the lines that summarise a placement, and the state of
   *Bake* from the stages' pairs and the server's answer. */

const noun = (count: number, one: string, many = `${one}s`): string =>
  `${count} ${count === 1 ? one : many}`

/* What is placed: the tattoo, how it is placed and the stages' pairs. */
export interface Placement {
  tattoo: Pick<Tattoo, 'name' | 'kind' | 'kept'> & { outline: Outline }
  mode: Mode
  /* What a cut names its photograph by. */
  photograph: string
  /* The automatic white point as a grey, once the preview has answered. */
  automatic: number | null
  seed: string
  /* The baked edit it is placed on, null for the render. */
  edit: number | null
  first: readonly Pair[]
  second: readonly Pair[]
  limb: readonly Point[] | null
  exclusions: readonly (readonly Point[])[]
  limits: TattooLimits
}

export interface Summary {
  image: string
  tattoo: string
  stages: string[]
  outlines: string[]
}

/** Return the lines that summarise `placement`: the image it is placed on, the tattoo, the
    pairs of each stage and the outlines. The tone is named for a cut, whose ink is read off a
    photograph, and for an upload only where it differs from the upload's default.
    e.g. a cut of 36 points, white 119, neutral at 1.6 ->
    "bow · cut from meadow_02 · outline 36 points · white 119 · neutral · depth 1.6" */
export function summary(placement: Placement): Summary {
  const { tattoo, mode, limits } = placement
  const { outline } = tattoo
  const source = tattoo.kind === 'cut' ? `cut from ${placement.photograph}` : `kept ${tattoo.kept.slice(0, 10)}`
  const parts = [tattoo.name, source, `outline ${noun(outline.points.length, 'point')}`]
  if (placement.automatic !== null) parts.push(`white ${greyOf(placement.automatic, outline.white)}`)
  const own = { neutral: outline.neutral, depth: outline.depth }
  if (tattoo.kind === 'cut' || differs(own, defaultTone('image', limits))) {
    if (outline.neutral) parts.push('neutral')
    parts.push(`depth ${outline.depth}`)
  }

  const stages =
    mode === 'two-stage'
      ? [
          `stage 1 · tattoo ↔ photograph · ${noun(placement.first.length, 'pair')}`,
          `stage 2 · photograph ↔ render · ${noun(placement.second.length, 'pair')}`,
        ]
      : mode === 'direct'
        ? [`tattoo ↔ render · ${noun(placement.second.length, 'pair')}`]
        : [`stage 2 · photograph ↔ render · ${noun(placement.second.length, 'pair')}`]

  const outlines = [
    ...(placement.limb ? [`limb · ${noun(placement.limb.length, 'point')} · keeps`] : []),
    ...placement.exclusions.map(
      (one, at) => `exclusion ${at + 1} · ${noun(one.length, 'point')} · removes`,
    ),
  ]

  return {
    image: placement.edit === null ? `seed ${placement.seed}` : `edit ${placement.edit} · seed ${placement.seed}`,
    tattoo: parts.join(' · '),
    stages,
    outlines: outlines.length > 0 ? outlines : ['no limb or exclusion'],
  }
}

export interface Fit {
  aspectRatio: string
  backgroundSize: string
  backgroundPosition: string
}

/* The percentage that puts `offset` of `whole` at the start of a frame `part` wide; 0 where
   the box fills the axis. */
const placed = (offset: number, whole: number, part: number): number =>
  whole > part ? (offset / (whole - part)) * 100 : 0

/** Return the style that shows the render's `box` filling a frame of the box's aspect ratio:
    the render is sized at its width over the box's, and placed by the box's offset over
    what is left of the render.
    e.g. the box 100 by 50 at 250, 275 on 1100 by 600 -> "100 / 50", "1100%", "25% 50%" */
export function fitted(box: Preview['box'], size: { width: number; height: number }): Fit {
  return {
    aspectRatio: `${box.width} / ${box.height}`,
    backgroundSize: `${(size.width / box.width) * 100}%`,
    backgroundPosition: `${placed(box.x, size.width, box.width)}% ${placed(box.y, size.height, box.height)}%`,
  }
}

/* What *Bake* is: waiting for pairs, ready, asking, refused with the server's words, or the
   bake queued as an edit. */
export interface BakeState {
  phase: 'waiting' | 'ready' | 'baking' | 'queued' | 'refused'
  text: string
  enabled: boolean
}

export interface BakeInput {
  mode: Mode
  first: Pairs
  second: Pairs
  limits: TattooLimits
  /* The bake has been asked and not answered. */
  asking: boolean
  /* The edit the server answered with, or null. */
  edit: number | null
  refusal: string | null
}

/* Why a stage lacks its pairs, naming the stage, or null when every stage has them. */
function lacking({ mode, first, second, limits }: BakeInput): string | null {
  if (mode === 'two-stage') {
    const early = forward(first, limits.floor_stage1)
    if (early !== null) return `stage 1 · ${early}`
  }
  const late = forward(second, mode === 'direct' ? limits.floor_direct : limits.floor_stage2)
  if (late === null) return null
  return `${mode === 'direct' ? 'tattoo ↔ render' : 'stage 2'} · ${late}`
}

/** Return the state of *Bake*: queued once answered, else waiting while a stage lacks its
    floor or holds a lone point, saying which.
    e.g. 5 stage-2 pairs against 8 -> "stage 2 · 8 pairs needed · 5 placed"; edit 3 ->
    "queued · edit 3 · next render session" */
export function bakeState(input: BakeInput): BakeState {
  if (input.edit !== null) {
    return { phase: 'queued', text: `queued · edit ${input.edit} · next render session`, enabled: false }
  }
  if (input.asking) return { phase: 'baking', text: 'baking…', enabled: false }
  const wait = lacking(input)
  if (wait !== null) return { phase: 'waiting', text: wait, enabled: false }
  if (input.refusal !== null) return { phase: 'refused', text: input.refusal, enabled: true }
  return { phase: 'ready', text: '', enabled: true }
}
