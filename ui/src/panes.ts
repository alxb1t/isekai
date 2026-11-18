/* Review's panes, left to right: the rail, the photograph and its caption, the
   sheet, and ④ Renders. On macOS `⌃H` `⌃L` alone move between them; elsewhere
   `h` `l` or `←` `→` do, outside a field (D25). */

import { type Command, type Key, plain } from './stores/keys'

/** One of Review's panes. */
export type Pane = 'rail' | 'source' | 'sheet' | 'renders'

export const PANES: Pane[] = ['rail', 'source', 'sheet', 'renders']

/** Where a pane is: `holds` is what an element inside it answers `closest` for, `entry` what
    the focus enters, and `within`, when set, what inside `entry` takes it. */
export interface PaneSelectors {
  holds: string
  entry: string
  within?: string
}

export const SELECTORS: Record<Pane, PaneSelectors> = {
  rail: { holds: '.rail', entry: '.rail__card--current' },
  source: { holds: '.source', entry: '.source' },
  sheet: { holds: '.form', entry: 'input.fragment' },
  renders: {
    holds: '.renders-block',
    entry: '.renders-block',
    within: 'button:not(:disabled), input',
  },
}

/** macOS's `⌃J` `⌃K`: `↓` `↑` from a field, which a tag field reads too. */
export const FIELD_DOWN: Key = { code: 'KeyJ', ctrl: true }
export const FIELD_UP: Key = { code: 'KeyK', ctrl: true }

/** Return the pane `step` from `at`, held at either end. e.g. ('rail', 1) -> 'source' */
export function nextPane(at: Pane, step: -1 | 1): Pane {
  const index = PANES.indexOf(at) + step
  return PANES[Math.min(Math.max(index, 0), PANES.length - 1)]
}

/** The panes in the order `paneOf` asks: ④ before the sheet, whose form holds it. */
const NESTED: Pane[] = ['rail', 'source', 'renders', 'sheet']

/** Return the pane an element sits in, or null. e.g. an element inside ④ -> 'renders' */
export function paneOf(element: { closest(selector: string): unknown } | null): Pane | null {
  if (!element) return null
  for (const pane of NESTED) if (element.closest(SELECTORS[pane].holds)) return pane
  return null
}

/** Return Review's pane keys, each running `move` with its direction. On macOS, where
    `⌃` is free of the window manager, `⌃H` `⌃L` alone, from a field or not, so `h` `l`
    and `←` `→` stay the pane's own; and there `⌃J` `⌃K` run `row`, the field below or
    above, as `↓` `↑` do in a field. Elsewhere `h` `l` or `←` `→`, outside a field (D25). */
export function paneKeys(
  mac: boolean,
  move: (step: -1 | 1) => void,
  row: (step: -1 | 1) => void,
): Command[] {
  if (!mac)
    return [
      { id: 'left', keys: plain('KeyH', 'ArrowLeft'), label: 'pane left', run: () => move(-1) },
      { id: 'right', keys: plain('KeyL', 'ArrowRight'), label: 'pane right', run: () => move(1) },
    ]
  return [
    {
      id: 'field-left',
      keys: [{ code: 'KeyH', ctrl: true }],
      label: 'pane left',
      run: () => move(-1),
      inField: true,
    },
    {
      id: 'field-right',
      keys: [{ code: 'KeyL', ctrl: true }],
      label: 'pane right',
      run: () => move(1),
      inField: true,
    },
    {
      id: 'field-down',
      keys: [FIELD_DOWN],
      label: 'next field',
      run: () => row(1),
      inField: true,
    },
    {
      id: 'field-up',
      keys: [FIELD_UP],
      label: 'previous field',
      run: () => row(-1),
      inField: true,
    },
  ]
}
