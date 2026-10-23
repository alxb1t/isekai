import type { HubCell } from './types'

/* What a click or ↵ on a hub cell does follows its stage, as the design spec's J2
   states: one table, so no template decides it on its own. */
export type Action = 'tick' | 'review' | 'sheet' | 'view' | 'none'

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
