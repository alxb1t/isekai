---
bump: minor
after: [0121-the-placement-core]
beside: [0120-the-bakes-in-the-app]
---

# The placement

The placement screen gains its stages: pair the tattoo with the photograph and the photograph with the render, see the warp live, and bake it.

Reading map: [design](design.md) holds the pairs, the preview, the composite and the placement record, [tasks](tasks.md) its phases.

## Why

The core keeps tattoos, outlines them and shows their ink. Nothing yet carries that ink onto a render. A prototype proved that clicked point pairs, a thin-plate warp and a Multiply give a composite faster and better than Krita, and the tattoo edit bakes a composite into a render.

This change is the rest of the screen: the stages that place the ink, the live preview that catches a bad click while it is made, the limb and exclusions that keep the ink on skin, and the bake that queues an edit request. Nothing here spends money or needs a pod.

## What Changes

- New requirement, *A tattoo's stage-1 pairs are kept per photograph*: `.tattoos/<name>/stage1/<digest>.json`, saved as sent, with the *not on this photo* flag.
- New requirement, *The placement preview is made on the server*: one `POST`, ink on white as a JPEG on a crop of the target, `no-store`.
- New requirement, *A bake writes the edit request and its placement record*: the composite, the edit's record and `<seed>.edit-<k>.placement.json`, never an image.
- New requirement, *A bake is placed on an image, and a later bake changes no earlier one*: a render or a baked edit, a new edit each time.
- New requirement, *A placement record goes with its edit*: listings skip it, a discard takes it.
- New requirement, *Pairs are placed by clicks on two images*: the waiting image, selection, drag, undo, delete, the floors.
- New requirement, *The live preview follows the pairs*: a second after a change, the latest answer wins, the last stays dimmed.
- New requirement, *The outline step goes forward to the stage its tattoo takes*: stage 1, the direct stage or stage 2.
- New requirement, *A tattoo not on this photo is paired with the render directly*: the pairs of stage 1 are kept.
- New requirement, *The render stage draws a limb outline and exclusions*: the ink kept inside the limb and removed under each exclusion.
- New requirement, *The review shows the tattoo placed and bakes it*: before and after, the summary, *Bake*.
- New requirement, *Leaving with a point unmatched asks first*: the Leave dialog.
- Modified requirement, *The placement screen has a route of its own per step*: the steps of the stages, and the step a mode skips.
- Modified requirement, *The picker lists the kept tattoos and takes an upload or a cut*: *ready for this photo*, *not on this photo*, and the step a card opens.
- Each new colour is a token in each theme; D53 is new, [D4](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children) is amended, and the design spec and the tattoo guide are edited where they live.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `tattoo`: the stage-1 pairs, the preview, the bake and its placement record. Added requirements only.
- `ui`: the stages, the preview, the limb and exclusions, the review and the Leave dialog; the screen's route and the picker read again.

## Impact

- New: `ui/src/pairs.ts`, `ui/src/preview.ts`, `ui/src/stages.ts`, `ui/src/outlines.ts`, `ui/src/review.ts`, `ui/src/leave.ts`, `ui/src/composables/usePlacing.ts`, `ui/src/components/PairPanel.vue`, `ui/src/components/PairList.vue`, `ui/src/components/StagePhoto.vue`, `ui/src/components/StageRender.vue`, `ui/src/components/ReviewBake.vue`, `ui/src/components/LeaveDialog.vue`, and a test beside each module.
- Changed: `isekai/pipeline/tattoos.py`, `isekai/pipeline/edit.py`, `isekai/shared/chain.py`, `isekai/foundation/artifacts.py`, `isekai/foundation/run.py`, `isekai/pipeline/generate.py`, `isekai/interface/run_view.py`, `isekai/interface/ui/app.py`, `config/tattoo.json`, `ui/src/api.ts`, `ui/src/types.ts`, `ui/src/tattoos.ts`, `ui/src/routes.ts`, `ui/src/views/Place.vue`, `ui/src/components/TattooPicker.vue`, `ui/src/components/OutlineStep.vue`, `ui/src/styles.css`, `ui/src/themes.css`.
- Tests: `tests/test_tattoo_placement.py`, `tests/test_edit_placement.py`, `tests/test_ui_placement.py`, `tests/test_tattoo_library.py`, `tests/test_run_view.py`, `tests/test_ui_tattoo.py`, `tests/test_chain.py`.
- Docs: `docs/decisions.md`, `docs/edit-tattoo.md`, `docs/modules.md`, `ui/design/spec.md`, `isekai/pipeline/README.md`, `isekai/shared/README.md`.
- No dependency, no flow, no pinned digest, no format version and no end-to-end test changes.

## Not in this change

- Automatic pairs, outlines, limb and masks, and the proposal step: when automatic placement is built.
- Keys on the placement screen, a minimap, *follow*, exposure and the tint view of the preview: when the screen has been used and shows which are useful.
- *Place a tattoo* on a baked image's large view: when that large view is in the default branch with this change.
- A bake's own large view and the chain listing, the Render dialog's bakes and the quote of a session of bakes: the bakes in the app.
- Keeping stage-2 pairs, limb and exclusions across a reload or a leave: when losing them is missed.
- Deleting or renaming a kept tattoo or a bake: when one is missed.
- Browser tests: the e2e tattoo version, on the scenarios the person names after using the screen.
- A pod phase: the person's own full tattoo test after this change's release.
