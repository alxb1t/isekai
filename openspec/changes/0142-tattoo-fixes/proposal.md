---
bump: minor
---

# Tattoo fixes

The fixes the person's acceptance test of *Place a tattoo* found, before the first bake.

Reading map: [design](design.md) holds the decisions and the test cost, [tasks](tasks.md) the phases: the picker, the
steps, the review and the soft edge.

## Why

The person placed a tattoo end to end and found rough edges all along it. A lit *Remove* read as a stuck button; the picker
showed nothing of the render; step ④ left most of its page empty; a fresh cut's first ask for pairs went out with
the old, empty outline and showed the server's raw words; the review stacked its crops under a full render; and the
ink's edge, enlarged onto the render, read as a saw-tooth.

Each fix is small. Together they change what the screen shows and what the bake draws, which is past a patch.

## What Changes

- **Remove** opens the confirmation dialog the render's deletion uses, *Remove this tattoo?*, and the two-press arm goes.
- **The picker** shows the render and its photograph at its top, side by side, and a cut's card shows its own crop.
- **The head** of the placement screen loses its thumbnail, on every step.
- **Step ②'s head** reads *outlined* as soon as a closed outline is saved.
- **Step ④'s panels** take the page's full height.
- **Step ④'s ask for pairs** waits for the saved outline, asks nothing with none, and a refusal shows one plain line.
- **The review** shows *before* and *after* side by side, fitted to their columns, with no render above them; the summary
  and the buttons stand in the column to the right, *Back* and *Bake* in one row.
- **The ink's edge** is antialiased for the outline and the exclusions, so the preview and the bake draw it soft.

Requirement by requirement:

- `ui` · *The picker lists the kept tattoos and takes an upload or a cut* is removed and *The picker shows the render and
  lists the kept tattoos, and takes an upload or a cut* is added: the render and photograph at the top, a cut's own crop,
  *Remove* in a dialog. The scenario *remove takes a second click* becomes *remove asks in a dialog*, and a scenario for
  the crop is added. The title changes because a modified requirement may not drop a scenario.
- `ui` · *The outline step shows the ink and keeps its white point and tone*: the head reads the save's answer.
- `ui` · *Stage 2 proposes its pairs when it opens with none* is removed and *Stage 2 proposes its pairs when it opens
  with none, once the saved outline is read* is added: the ask waits for the saved outline and a refusal is one plain
  line. The scenario *a refusal shows its words…* is re-keyed, and a scenario for the wait is added.
- `ui` · *The review shows the tattoo placed and bakes it*: the crops fitted, side by side, no third image, the buttons
  in a row; a scenario for the fit is added.
- `ui` · *The placement screen declares undo, redo and close and no other key*: the confirmation dialog declares its own
  overlay keys while it is open.
- `tattoo` · *Ink is placed by thin-plate splines*: a polygon's mask is antialiased; scenarios for the mask's edge and an exclusion's edge are added.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`: the picker, the outline step's head, stage 2's ask, the review and the placement screen's keys.
- `tattoo`: the polygon mask of the ink, the limb and the exclusions.

## Impact

- UI, new: `ui/src/confirm.ts` with `ui/src/confirm.test.ts`, `ui/src/components/ConfirmDialog.vue` and
  `ui/src/components/CutImage.vue`. Deleted: `ui/src/components/DeleteDialog.vue`.
- UI, edited: `ui/src/components/TattooPicker.vue`, `ui/src/components/OutlineStep.vue`,
  `ui/src/components/StageRender.vue`, `ui/src/components/ReviewBake.vue`, `ui/src/views/Place.vue`,
  `ui/src/views/RenderLarge.vue`, `ui/src/composables/usePlacing.ts`, `ui/src/tattoos.ts`, `ui/src/propose.ts`,
  `ui/src/review.ts` and `ui/src/app.css`.
- UI tests, edited: `ui/src/tattoos.test.ts`, `ui/src/nokeys.test.ts`, `ui/src/propose.test.ts`,
  `ui/src/review.test.ts` and `ui/src/composables/usePlacing.test.ts`.
- Python: `isekai/shared/chain.py` and its tests `tests/test_chain.py` and `tests/test_tattoo_placement.py`.
- Docs: `ui/design/spec.md`, `docs/edit-tattoo.md` and `isekai/shared/README.md`.
- Specs: the `ui` and `tattoo` deltas of this change.

## Not in this change

- A brush eraser for the ink.
- The stray pair a later press placed: the closing press places no pair, and *point 17 has no match* already says so.
- The render's deletion's behaviour: its dialog becomes the shared one and nothing else about it moves.
- A server change: the picker reads each cut's outline and ink view through the routes that stand.
