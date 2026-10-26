/* Review's panes, left to right: the rail, the photograph and its caption, the
   sheet, and ④ Renders. `h` `l` or `←` `→` move between them outside a field (D25). */

import { type Command, plain } from './stores/keys'

/** One of Review's panes. */
export type Pane = 'rail' | 'source' | 'sheet' | 'renders'

export const PANES: Pane[] = ['rail', 'source', 'sheet', 'renders']

/** Return the pane `step` from `at`, held at either end. e.g. ('rail', 1) -> 'source' */
export function nextPane(at: Pane, step: -1 | 1): Pane {
  const index = PANES.indexOf(at) + step
  return PANES[Math.min(Math.max(index, 0), PANES.length - 1)]
}

/** Return Review's pane keys, each running `move` with its direction: `h` `l` or
    `←` `→` outside a field, and on macOS, where `⌃` is free of the window manager,
    `⌃H` `⌃L` from inside one, as a field keeps `h` and `l` as text; and there `⌃J`
    `⌃K` run `row`, the field below or above, as `↓` `↑` do in a field (D25). */
export function paneKeys(
  mac: boolean,
  move: (step: -1 | 1) => void,
  row: (step: -1 | 1) => void,
): Command[] {
  const outside: Command[] = [
    { id: 'left', keys: plain('KeyH', 'ArrowLeft'), label: 'pane left', run: () => move(-1) },
    { id: 'right', keys: plain('KeyL', 'ArrowRight'), label: 'pane right', run: () => move(1) },
  ]
  if (!mac) return outside
  return [
    ...outside,
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
      keys: [{ code: 'KeyJ', ctrl: true }],
      label: 'next field',
      run: () => row(1),
      inField: true,
    },
    {
      id: 'field-up',
      keys: [{ code: 'KeyK', ctrl: true }],
      label: 'previous field',
      run: () => row(-1),
      inField: true,
    },
  ]
}
