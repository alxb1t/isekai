/* Review's panes, left to right: the rail, the photograph and its caption, the
   sheet, and ④ Renders. `h` `l` or `←` `→` move between them outside a field (D25). */

/** One of Review's panes. */
export type Pane = 'rail' | 'source' | 'sheet' | 'renders'

export const PANES: Pane[] = ['rail', 'source', 'sheet', 'renders']

/** Return the pane `step` from `at`, held at either end. e.g. ('rail', 1) -> 'source' */
export function nextPane(at: Pane, step: -1 | 1): Pane {
  const index = PANES.indexOf(at) + step
  return PANES[Math.min(Math.max(index, 0), PANES.length - 1)]
}
