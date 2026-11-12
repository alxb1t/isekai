/* What a press on a panel does, and the cursor that says so. Shift places, a plain press
   on a point moves it, and a plain press elsewhere pans. */

import type { Point } from './types'

export type Gesture = 'place' | 'move' | 'pan'

export type Cursor = 'crosshair' | 'grab' | 'grabbing'

/** Return what a press does: Shift places, else a `grabbed` index moves it, else the view pans.
    e.g. Shift up on vertex 2 -> "move"; Shift up on bare image -> "pan" */
export function gestureOf(shift: boolean, grabbed: number | null): Gesture {
  if (shift) return 'place'
  return grabbed === null ? 'pan' : 'move'
}

const MODIFIERS = new Set(['Control', 'Meta', 'Shift', 'Alt'])

/** Return whether a key press ends a press under way: a command key (Ctrl or Meta with a key
    that is no modifier), as undo and redo are, which change the history a drag goes on writing.
    e.g. Meta+Z -> true; Shift alone -> false */
export function endsPress(key: { key: string; ctrlKey: boolean; metaKey: boolean }): boolean {
  return (key.ctrlKey || key.metaKey) && !MODIFIERS.has(key.key)
}

/** What a pointer move did to the press under way. */
export type Step =
  | { kind: 'hover' }
  | { kind: 'still' }
  | { kind: 'drag'; index: number; fresh: boolean }
  | { kind: 'pan'; dx: number; dy: number }

/** What a release of the press ends as: whether it was a click, and the Shift it began with. */
export interface Release {
  click: boolean
  shift: boolean
}

interface Held {
  start: Point
  last: Point
  gesture: Gesture
  grabbed: number | null
  shift: boolean
  moved: boolean
  fresh: boolean
}

/** Return the press under way on a panel, one gesture from its press to its release or its end
    on a command key. A move past `slop` of the press is a drag of `grabbed` or a pan, its first
    drag step `fresh` and the rest not; within it, nothing.
    e.g. down on vertex 1, two moves -> drag fresh, drag not fresh */
export function pressing(slop: number) {
  let held: Held | null = null
  return {
    get held(): boolean {
      return held !== null
    },
    down(at: Point, shift: boolean, grabbed: number | null): void {
      const gesture = gestureOf(shift, grabbed)
      held = { start: at, last: at, gesture, grabbed, shift, moved: false, fresh: true }
    },
    move(at: Point): Step {
      if (!held) return { kind: 'hover' }
      if (!held.moved && Math.hypot(at[0] - held.start[0], at[1] - held.start[1]) <= slop) return { kind: 'still' }
      held.moved = true
      const last = held.last
      held.last = at
      if (held.gesture === 'move' && held.grabbed !== null) {
        const step: Step = { kind: 'drag', index: held.grabbed, fresh: held.fresh }
        held.fresh = false
        return step
      }
      if (held.gesture === 'pan') return { kind: 'pan', dx: at[0] - last[0], dy: at[1] - last[1] }
      return { kind: 'still' }
    },
    up(): Release | null {
      const was = held
      held = null
      return was && { click: !was.moved, shift: was.shift }
    },
    /** End the press on a command key, so no drag goes on writing past a history change. */
    key(event: { key: string; ctrlKey: boolean; metaKey: boolean }): void {
      if (held && endsPress(event)) held = null
    },
    cancel(): void {
      held = null
    },
  }
}

/** Return the cursor: the grabbing hand while a pan or a move is `active`, else the crosshair
    under Shift, else the hand. e.g. Shift held, nothing under way -> "crosshair" */
export function cursorOf(shift: boolean, active: boolean): Cursor {
  if (active) return 'grabbing'
  return shift ? 'crosshair' : 'grab'
}
