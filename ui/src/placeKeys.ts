import { type Command, isControl, modded, plain, shifted } from './stores/keys'

/* The placement screen's keys: undo, redo and, where an outline is drawn, close. The outline
   step and the stages that hold pairs declare them on the screen; nothing else there does. */

/** What each key runs; a stage with no outline to close leaves `close` out. */
export interface PlaceActions {
  undo: () => void
  redo: () => void
  close?: () => void
}

/* The focused element, read through `globalThis` so a node test has none. */
const focused = (): EventTarget | null =>
  (globalThis as { document?: Document }).document?.activeElement ?? null

/** Return the commands `undo` on Mod+Z, `redo` on ⇧Mod+Z and, with `close`, `close` on ↵.
    A text field keeps its own keys, and a focused control keeps ↵.
    e.g. on a Mac, undo and redo read "⌘Z" and "⇧⌘Z" */
export function placeCommands({ undo, redo, close }: PlaceActions): Command[] {
  const commands: Command[] = [
    { id: 'undo', keys: [modded('KeyZ')], label: 'undo', run: undo },
    { id: 'redo', keys: [{ ...shifted('KeyZ'), mod: true }], label: 'redo', run: redo },
  ]
  if (close) {
    commands.push({
      id: 'close',
      keys: plain('Enter'),
      label: 'close the outline',
      run: close,
      when: () => !isControl(focused()),
    })
  }
  return commands
}
