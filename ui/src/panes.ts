/* Review's panes, left to right: the rail, the photograph and its caption, the
   sheet, and ④ Renders. On macOS `⌃H` `⌃L` alone move between them; elsewhere
   `h` `l` or `←` `→` do, outside a field (D25). */

import { type Command, type Key, plain } from './stores/keys'

/** One of Review's panes. */
export type Pane = 'rail' | 'source' | 'sheet' | 'renders'

export const PANES: Pane[] = ['rail', 'source', 'sheet', 'renders']

/** macOS's `⌃J` `⌃K`: `↓` `↑` from a field, which a tag field reads too. */
export const FIELD_DOWN: Key = { code: 'KeyJ', ctrl: true }
export const FIELD_UP: Key = { code: 'KeyK', ctrl: true }

/** Return the pane `step` from `at`, held at either end. e.g. ('rail', 1) -> 'source' */
export function nextPane(at: Pane, step: -1 | 1): Pane {
  const index = PANES.indexOf(at) + step
  return PANES[Math.min(Math.max(index, 0), PANES.length - 1)]
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
