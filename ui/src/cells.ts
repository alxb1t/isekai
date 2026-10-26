import type { HubCell } from './types'

/* What a click or ↵ on a hub cell does follows its stage, as the design spec's J2
   states: one table, so no template decides it on its own. */
export type Action = 'tick' | 'review' | 'sheet' | 'view' | 'none'

/** A cell whose run holds no directory for the flow, or a source with no run. */
export const EMPTY_CELL: Readonly<HubCell> = {
  stage: null,
  renders: 0,
  refusal: null,
  status: null,
  newest: null,
  short: null,
  images: [],
}

export interface CellAction {
  action: Action
  hint: string | null
}

/** Return what a click on `cell` does, and the hint its focus shows. */
export function action(cell: HubCell): CellAction {
  switch (cell.stage) {
    case null:
    case 'assigned':
      return { action: 'tick', hint: null }
    case 'tagged':
    case 'unreadable':
      return { action: 'none', hint: null }
    case 'sheet':
    case 'draft':
      return { action: 'review', hint: '↵ review' }
    case 'approved':
    case 'rendered':
      return cell.newest === null
        ? { action: 'sheet', hint: '↵ review' }
        : { action: 'view', hint: '↵ view' }
  }
}

/** Return the rows a tick lands on: a click's own row; space's, the selection's.

    A pointer lands on one cell, so a click ticks that cell whatever rows ⇧↑↓
    selected; space ticks the focused column for every selected row. */
export function targets(selected: ReadonlySet<number>, row: number, pointer: boolean): number[] {
  return pointer || selected.size === 0 ? [row] : [...selected]
}

/** Return whether a click on a cell runs its action.

    A click inside the cell's refusal, or one that ends a text selection, is
    reading or copying the fix, never a tick. */
export function clicks(
  target: { closest(selector: string): unknown } | null,
  selection: string,
): boolean {
  return selection === '' && !target?.closest('.hub__refusal')
}

/** An image of a cell, by its approval's version and its seed. */
export interface CellImage {
  version: number
  seed: string
}

/** Return where *Compare with…* goes from `version`'s `seed`: straight to the
    cell's one other image, else the pick, on that seed's newest older version,
    `compare`, else on the image before this one, indexed among the others.

    e.g. ([v1·7, v2·7], 2, '7', 1) -> {compare: v1·7} */
export function pick(
  images: CellImage[],
  version: number,
  seed: string,
  compare: number | null,
): { at: number } | { compare: CellImage } {
  const others = images.filter((one) => one.version !== version || one.seed !== seed)
  if (others.length === 1) return { compare: others[0] }
  const paired = others.findIndex((one) => one.version === compare && one.seed === seed)
  if (paired >= 0) return { at: paired }
  const here = images.findIndex((one) => one.version === version && one.seed === seed)
  return { at: Math.max(here - 1, 0) }
}
