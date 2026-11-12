import type { Outline, Tattoo } from './types'

/* What the picker and the outline step read of a tattoo, as plain functions. */

export interface Card {
  state: 'outlined' | 'not outlined'
  /* What it came from: when it was kept and the size it came with, or its photograph. */
  source: string
  /* A cut of another photograph is listed and cannot be chosen on this render. */
  choosable: boolean
  reason: string | null
}

/** Return what a card shows of `tattoo` on the render whose run digest is `digest`.
    e.g. an upload kept on 2026-11-12 -> source "kept 2026-11-12" */
export function card(tattoo: Tattoo, digest: string): Card {
  const state = tattoo.outlined ? 'outlined' : 'not outlined'
  if (tattoo.kind === 'cut') {
    const source = `from photograph ${tattoo.cut_from}`
    const other = tattoo.cut_from !== digest
    return { state, source, choosable: !other, reason: other ? `${source}, not this render's` : null }
  }
  const scaled = tattoo.downscaled_from
  const was = scaled ? ` · downscaled from ${scaled[0]}×${scaled[1]}` : ''
  return { state, source: `kept ${tattoo.kept.slice(0, 10)}${was}`, choosable: true, reason: null }
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

/** Tell whether the tone differs from `defaults`, the kind's, so *Reset* is offered. */
export function differs(tone: Tone, defaults: Tone): boolean {
  return tone.neutral !== defaults.neutral || tone.depth !== defaults.depth
}

/** Return the size of a closed outline's box on its image, as the cut's source line reads it.
    e.g. a box of 412.4 by 300.6 -> "412×301" */
export function inkSize(box: { width: number; height: number } | null): string | null {
  return box ? `${Math.round(box.width)}×${Math.round(box.height)}` : null
}
