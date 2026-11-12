import { type Step, startStep } from './stages'
import type { Outline, Point, Stage1, Tattoo, TattooLimits } from './types'

/* What the picker and the outline step read of a tattoo, as plain functions. */

export interface Card {
  state: 'outlined' | 'not outlined' | 'ready for this photograph'
  /* What it came from: when it was kept and the size it came with, or its photograph. */
  source: string
  /* An upload's stage 1 on this photograph: its pairs, or the flag; null if never placed. */
  stage: string | null
  /* The card offers *not on this photo*: an upload's does, a cut's does not. */
  offers: boolean
  /* The step choosing the card opens. */
  opens: Step
}

/** Tell whether a tattoo is ready for the photograph: outlined and, if uploaded, holding the
    floor of stage-1 pairs on it or flagged *not on this photo*. */
export function ready(tattoo: Tattoo, state: Stage1 | undefined, floor: number): boolean {
  if (!tattoo.outlined) return false
  return tattoo.kind === 'cut' || state?.not_on_photo === true || (state?.pairs.length ?? 0) >= floor
}

/** Return the sub-line of an upload's stage 1: `stage 1 · 6 pairs`, or *not on this photo*. */
export function stageLine(state: Stage1 | undefined): string | null {
  if (!state) return null
  if (state.not_on_photo) return 'not on this photo'
  const count = state.pairs.length
  return `stage 1 · ${count} ${count === 1 ? 'pair' : 'pairs'}`
}

/** Return the path that lists the tattoos of the render whose run digest is `digest`.
    e.g. "a1b2c3d4e5f6" -> "/api/tattoos?digest=a1b2c3d4e5f6" */
export function tattoosPath(digest: string): string {
  return `/api/tattoos?${new URLSearchParams({ digest })}`
}

/** Return what a card shows of `tattoo` on the render whose run digest is `digest`, with the
    tattoo's stage-1 `held` on that photograph and the stage-1 `floor`.
    e.g. an upload kept on 2026-11-12 -> source "kept 2026-11-12" */
export function card(
  tattoo: Tattoo,
  digest: string,
  held: Stage1 | undefined,
  floor: number,
): Card {
  const placed = ready(tattoo, held, floor)
  const state = placed ? 'ready for this photograph' : tattoo.outlined ? 'outlined' : 'not outlined'
  const opens = startStep(tattoo, held, floor)
  if (tattoo.kind === 'cut') {
    return { state, source: `from photograph ${tattoo.cut_from}`, stage: null, offers: false, opens }
  }
  const scaled = tattoo.downscaled_from
  const was = scaled ? ` · downscaled from ${scaled[0]}×${scaled[1]}` : ''
  return {
    state,
    source: `kept ${tattoo.kept.slice(0, 10)}${was}`,
    stage: stageLine(held),
    offers: true,
    opens,
  }
}

/** Return what a press of *Remove* on the card `name` does when `armed` is the card armed
    before it: the first press arms the card, the second on it removes. e.g. (null, "bow") ->
    { armed: "bow", remove: false }; ("bow", "bow") -> { armed: null, remove: true } */
export function armRemoval(
  armed: string | null,
  name: string,
): { armed: string | null; remove: boolean } {
  return armed === name ? { armed: null, remove: true } : { armed: name, remove: false }
}

/** Return the line under a picker form's heading: what the form takes. */
export function formLine(form: 'upload' | 'cut'): string {
  return form === 'upload'
    ? "the tattoo's design on its own — a flat image, not a photo of skin"
    : "the tattoo as it shows on this render's photograph"
}

/** Return the name an upload starts under: the file's stem, or `<cut>_closeup` when it
    replaces a cut. e.g. "IMG_5521.heic" -> "IMG_5521"; instead of "bow" -> "bow_closeup" */
export function uploadName(file: string, instead: string | null = null): string {
  if (instead !== null) return `${instead}_closeup`
  const dot = file.lastIndexOf('.')
  return dot > 0 ? file.slice(0, dot) : file
}

/** Return where a refusal is shown: beside the name when it asks for another name, else on the file. */
export function refusalField(refusal: string): 'name' | 'file' {
  return /another name/.test(refusal) ? 'name' : 'file'
}

/** Return why the ink view, the white point and the tone wait, or null when they do not. */
export function controlsWait(outline: Pick<Outline, 'closed'>): string | null {
  return outline.closed ? null : 'outline open'
}

/** Return the one line that says how to close an open outline, or null once it is closed.
    e.g. an open outline of one vertex -> "close the outline on its first point · 1 point" */
export function closeLine(outline: { closed: boolean; points: readonly Point[] }): string | null {
  if (outline.closed) return null
  const count = outline.points.length
  return `close the outline on its first point · ${count} ${count === 1 ? 'point' : 'points'}`
}

/** Return the grey a scale shows against the automatic grey, a whole number.
    e.g. an automatic 200 at a scale of 0.9 -> 180 */
export function greyOf(automatic: number, scale: number): number {
  return Math.round(automatic * scale)
}

/** Return the scale a grey set by hand stores against the automatic grey, the grey held
    from 1 to 255 so the scale is never zero. e.g. 180 against 200 -> 0.9 */
export function scaleOf(grey: number, automatic: number): number {
  if (automatic <= 0) return 1
  return Math.max(1, Math.min(255, grey)) / automatic
}

/** Return `auto` for a scale of one and `set by hand` for any other. */
export function whiteState(scale: number): 'auto' | 'set by hand' {
  return scale === 1 ? 'auto' : 'set by hand'
}

export interface Tone {
  neutral: boolean
  depth: number
}

/** Return the tone a kind starts at: a cut neutral at the photograph's depth, an upload
    in colour at the image's. e.g. a cut with a photo depth of 1.6 -> neutral on, depth 1.6 */
export function defaultTone(
  kind: Tattoo['kind'],
  limits: Pick<TattooLimits, 'photo_depth' | 'image_depth'>,
): Tone {
  return kind === 'cut'
    ? { neutral: true, depth: limits.photo_depth }
    : { neutral: false, depth: limits.image_depth }
}

/** Tell whether the tone differs from `defaults`, the kind's, so *Reset* is offered. */
export function differs(tone: Tone, defaults: Tone): boolean {
  return tone.neutral !== defaults.neutral || tone.depth !== defaults.depth
}

/** Return the size of a closed outline's box on its image, as the cut's source line reads it.
    e.g. a box of 412.4 by 300.6 -> "412×301" */
export function inkSize(box: { width: number; height: number } | null): string | null {
  return box ? `${Math.round(box.width)}×${Math.round(box.height)}` : null
}
