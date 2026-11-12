/* What a press on a panel does, and the cursor that says so. Shift places, a plain press
   on a point moves it, and a plain press elsewhere pans. */

export type Gesture = 'place' | 'move' | 'pan'

export type Cursor = 'crosshair' | 'grab' | 'grabbing'

/** Return what a press does: Shift places, else a `grabbed` index moves it, else the view pans.
    e.g. Shift up on vertex 2 -> "move"; Shift up on bare image -> "pan" */
export function gestureOf(shift: boolean, grabbed: number | null): Gesture {
  if (shift) return 'place'
  return grabbed === null ? 'pan' : 'move'
}

/** Return the cursor: the grabbing hand while a pan or a move is `active`, else the crosshair
    under Shift, else the hand. e.g. Shift held, nothing under way -> "crosshair" */
export function cursorOf(shift: boolean, active: boolean): Cursor {
  if (active) return 'grabbing'
  return shift ? 'crosshair' : 'grab'
}
