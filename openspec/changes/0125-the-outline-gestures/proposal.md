---
bump: minor
debt: [0123·S4]
---

# The outline gestures

The outline, pair and limb steps answer the hand: Shift places, the plain mouse pans, ⌘Z undoes, the outline closes.

Reading map: [design](design.md) holds the press rule, the placing rule, the key store's commands and the test cost, [tasks](tasks.md) builds the gestures first and then the keys and words.

## Why

The person's first session on *Place a tattoo* at `v0.83.0` (wish list W8–W12) met one cursor for every gesture, a close that a near miss turned into a hidden stacked point, no redo, no key, and *outline open* said at each control. W12, the outline that cannot be closed, blocks the next screen. This version is the page alone: it needs no server change.

## What Changes

- `ImagePanel.vue` applies one press rule: with Shift held a click places and the cursor is a crosshair; with Shift up a drag pans, a drag on a point moves it and a double click on a point removes it. The cursor is the hand, and the grabbing hand while a pan is under way.
- A shift-click on the outline, and on the render step's limb and exclusion sketch, closes on the first point, inserts on an edge within reach, or adds. A click within reach of a point never adds a point there.
- The outline and the pair editor keep a redo (`future`) beside their undo; ⌘Z undoes and ⇧⌘Z redoes (Ctrl off a Mac), and Enter closes an outline that can close, all through the app's key store and listed with the app's keys.
- The three gesture hint lines go; the three per-control *outline open* go for one line above the controls, *close the outline on its first point · N points*; the first point grows and reads *close* under the pointer once the outline can close.
- Returning to a tattoo after its pairs were cleared proposes again ([0123·S4](design.md#d9)).

Requirements the delta touches, one line each:

- REMOVED *The placement screen holds no key of its own*; ADDED *The placement screen declares undo, redo and close and no other key*.
- MODIFIED *The panel zooms at the pointer, pans by a drag, and fits or shows 1:1*: Shift places, a plain drag pans, the cursor says which.
- MODIFIED *An outline is clicked, closed on its first point and edited by dragging*: the Shift rule, a near miss, redo, the floor.
- MODIFIED *The outline step shows the ink and keeps its white point and tone*: one line, not three.
- MODIFIED *Pairs are placed by clicks on two images*: a shift-click places, a plain click selects, redo.
- MODIFIED *The render stage draws a limb outline and exclusions*: the same Shift rule, Enter closes.
- MODIFIED *Stage 2 proposes its pairs when it opens with none*: returning to a tattoo asks again.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`: the panel, the outline editor, the outline step, the pair editor, the render stage, the placement keys and stage 2's proposal.

## Impact

- `ui/src/`: `press.ts`, `placeKeys.ts`, `polygon.ts`, `pairs.ts`, `tattoos.ts`, `composables/usePlacing.ts`, `components/ImagePanel.vue`, `OutlineStep.vue`, `StagePhoto.vue`, `StageRender.vue`, `PairList.vue`, `app.css`, and their node tests; `nokeys.test.ts` narrows.
- `docs/edit-tattoo.md` and `ui/design/spec.md` name the gestures and the keys.
- No server, run-file, manifest or dependency change. No decision in force changes.

## Not in this change

- Cuts per photograph, *Remove* on a card, the picker's lines and D52: the version that cuts them shares only the ui spec and `CHANGELOG.md` with this one.
- Renaming a tattoo.
- Mounting components in the UI tests: the node tests cover the pure rules.
- A redo button: the keys are the way to redo.
