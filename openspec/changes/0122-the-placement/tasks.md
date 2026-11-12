# The placement — tasks

The phases: the stages with the preview, the limb and exclusions, the bake, the Leave dialog, the docs. No phase is a person's, and none spends money.

## Progress

- [x] 1 — Stages · hard
- [x] 2 — Limb and exclusions · moderate
- [x] 3 — Bake · hard
- [ ] 4 — Leave · moderate
- [ ] 5 — Docs · moderate

## 1 — Stages

- [x] 1.1 **HALT CHECK** The core's chain and ink view are built: its tests carry `chain_composite` and `ink_view`.
  Verify: `uv run pytest tests/test_chain.py tests/test_tattoo_library.py -k "chain_composite or ink_view"` passes.
- [x] 1.2 **HALT CHECK** The core's panel, outline editor, picker, outline step and screen exist.
  Verify: `ls ui/src/polygon.ts ui/src/components/ImagePanel.vue ui/src/components/TattooPicker.vue ui/src/components/OutlineStep.vue ui/src/views/Place.vue` prints each path.
- [x] 1.3 Add to `config/tattoo.json` the keys `floor_stage1`, `floor_stage2`, `floor_direct`, `preview_floor`, `preview_margin`, `preview_wait_ms`, `pair_radius` and `region_min` 3 per [D2](design.md#d2), and make `tattoo_config` in `tests/test_tattoo_library.py` read each.
  Verify: `uv run pytest tests/test_tattoo_library.py -k tattoo_config` passes.
- [x] 1.4 Add to `isekai/pipeline/tattoos.py` `read_stage1`, `save_stage1` and `stage1_states` per [D1](design.md#d1); tests in `tests/test_tattoo_placement.py` carry `placement_stage1`.
  Verify: `uv run pytest tests/test_tattoo_placement.py -k placement_stage1` passes.
- [x] 1.5 Add to `isekai/shared/chain.py` `place` and `flatten` per [D3](design.md#d3), over `lookup`, `polygon_mask` and `clip`, numpy and Pillow imported inside; tests in `tests/test_chain.py` carry `chain_place`.
  Verify: `uv run pytest tests/test_chain.py -k chain_place` passes.
- [x] 1.6 Add to `tattoos.py` `mode_of`, `ink_layer`, `Preview` and `preview` per [D2](design.md#d2), [D3](design.md#d3) and [D4](design.md#d4), and make `ink_view` flatten `ink_layer`'s result with the values the page sent; tests carry `placement_preview`.
  Verify: `uv run pytest tests/test_tattoo_placement.py tests/test_tattoo_library.py -k "placement_preview or ink_view"` passes.
- [x] 1.7 Add to `isekai/interface/ui/app.py` `GET` and `PUT /api/tattoos/{name}/stage1/{digest}`, the `digest` query and the new limits on `GET /api/tattoos`, and the routes in the module's route table; update the list's expectation in `tests/test_ui_tattoo.py` carrying `tattoo_route_read`; tests in `tests/test_ui_placement.py` carry `placement_route_stage1`.
  Verify: `uv run pytest tests/test_ui_placement.py tests/test_ui_tattoo.py -k "placement_route_stage1 or tattoo_route_read"` passes.
- [x] 1.8 Add to `app.py` `POST /api/c/{collection}/tattoos/{name}/preview` per [D4](design.md#d4): the run's photograph as `held(...).run.photo`, the target as `rendered(...)` resolves a render or, for an `edit`, `edit_files(group, seed, edit)[0]`, a JPEG with `no-store`, `X-Preview-Box` and `X-Ink-White`; tests carry `placement_route_preview`.
  Verify: `uv run pytest tests/test_ui_placement.py -k placement_route_preview` passes.
- [x] 1.9 Hold that the guard answers each new route and no route deletes or renames a tattoo; tests carry `placement_route_guard`.
  Verify: `uv run pytest tests/test_ui_placement.py -k placement_route_guard` passes.
- [x] 1.10 Hold that `app.py` writes no file of its own.
  Verify: `uv run pytest tests/test_ui.py -k invariant` passes.
- [x] 1.11 Hold that the entry point's import graph reaches no wheel and the layers hold.
  Verify: `uv run pytest tests/test_pipeline_cli.py tests/test_layers.py` passes.
- [x] 1.12 Add to `ui/src/types.ts` `Pair`, `Stage1` and `Preview`, and to `ui/src/api.ts` `stageOne`, `saveStageOne` and `export function placementPreview`, which reads the headers of [D4](design.md#d4).
  Verify: `git grep -n "export function placementPreview" ui/src/api.ts` prints it.
- [x] 1.13 Add `ui/src/pairs.ts` per [D8](design.md#d8): `clicked`, `moved`, `deleted`, `undone`, `cleared`, `selected`, `lone` and `forward`; its tests in `ui/src/pairs.test.ts` bind through `spec`.
  Verify: `npm --prefix ui run test -- src/pairs.test.ts` passes.
- [x] 1.14 Add `ui/src/preview.ts` per [D8](design.md#d8): `due`, `asked`, `answered`, `dimmed`, `refused` and `previewable`; its tests in `ui/src/preview.test.ts` bind through `spec`.
  Verify: `npm --prefix ui run test -- src/preview.test.ts` passes.
- [x] 1.15 Add `ui/src/stages.ts` per [D8](design.md#d8) and [D9](design.md#d9): `modeOf`, `stepsOf`, `forwardOf`, `startStep` and `skipped`; its tests in `ui/src/stages.test.ts` bind through `spec`, among them the skipped step's redirect.
  Verify: `npm --prefix ui run test -- src/stages.test.ts` passes.
- [x] 1.16 Add `ui/src/composables/usePlacing.ts` per [D7](design.md#d7): the tattoo, the stage-1 pairs read, the pairs held, and a `saveStageOne` on each change of the complete stage-1 pairs; its tests in `ui/src/composables/usePlacing.test.ts` bind through `spec`.
  Verify: `npm --prefix ui run test -- src/composables/usePlacing.test.ts` passes.
- [x] 1.17 Add `ui/src/components/PairPanel.vue` (the panel with the point markers, the waiting edge, the preview multiplied over it, its opacity and a hide control), `PairList.vue`, `StagePhoto.vue`, the stage-1 step, and `StageRender.vue`, the render step, whose left panel is the photograph for a two-stage tattoo or a cut and the tattoo's ink view for a direct one; each ends in the forward action of `forward` in `pairs.ts`, waiting with its reason, per [D8](design.md#d8).
  Verify: `ls ui/src/components/PairPanel.vue ui/src/components/PairList.vue ui/src/components/StagePhoto.vue ui/src/components/StageRender.vue` prints each path.
- [x] 1.18 Per [D9](design.md#d9) add the steps `photo` and `render` to the step set of `ui/src/routes.ts`; fix any test in `ui/src/viewkey.test.ts` that names either as an unknown step, and add one there that both resolve to the `place` route.
  Verify: `npm --prefix ui run test -- src/viewkey.test.ts` passes.
- [x] 1.19 Give `ui/src/views/Place.vue` the `usePlacing`, a stepper from `stepsOf`, `StagePhoto` for `photo`, `StageRender` for `render`, and the replace of the route by `skipped`'s step once the tattoo is read.
  Verify: `git grep -n "skipped" -- ui/src/views` prints the use.
- [x] 1.20 In `ui/src/tattoos.ts` add the state *ready for this photograph*, the stage-1 sub-line and the card's `startStep`; in `ui/src/components/TattooPicker.vue` the *not on this photo* tick on an upload's card, saved through `saveStageOne`, and the card opening `startStep`; in `ui/src/components/OutlineStep.vue` the forward action from `forwardOf`; tests in `ui/src/tattoos.test.ts` bind through `spec`.
  Verify: `npm --prefix ui run test -- src/tattoos.test.ts` passes.
- [x] 1.21 Hold the browser's types.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [x] 1.22 Hold the browser's unit tests.
  Verify: `uv run python -m tools.test_ui` exits 0.

## 2 — Limb and exclusions

- [x] 2.1 Declare `--limb-fill` and `--exclusion-fill` per [D10](design.md#d10) in the Nocturne block of `ui/src/styles.css`, `:root, [data-theme="nocturne"]`, and in each Catppuccin block of `ui/src/themes.css`.
  Verify: `git grep -c -e "--limb-fill" -e "--exclusion-fill" -- ui/src/styles.css ui/src/themes.css` prints `ui/src/styles.css:2` and `ui/src/themes.css:8`.
- [x] 2.2 Hold that each theme sets every token Nocturne does.
  Verify: `npm --prefix ui run test -- src/themes.test.ts` passes.
- [x] 2.3 Make `preview` in `tattoos.py` refuse a limb or an exclusion with fewer points than `region_min`, naming the region; tests carry `placement_region`.
  Verify: `uv run pytest tests/test_tattoo_placement.py -k placement_region` passes.
- [x] 2.4 Add `ui/src/outlines.ts` per [D8](design.md#d8): `begun`, `closed`, `rows` and `held` over `polygon.ts`, the floor read from the list's limits; its tests in `ui/src/outlines.test.ts` bind through `spec`.
  Verify: `npm --prefix ui run test -- src/outlines.test.ts` passes.
- [x] 2.5 Draw the limb and the exclusions in `PairPanel.vue` from `--limb-fill`, `--exclusion-fill` and `--accent-ink`, the open outline's dashed segment included.
  Verify: `git grep -n -e "--limb-fill" -e "--exclusion-fill" -- ui/src/components` prints the uses.
- [x] 2.6 Add to `StageRender.vue` the outlines' rows with *Draw limb*, *Draw exclusion* and *Edit*, the pair editor held while an outline is drawn, and the limb and exclusions sent with each preview.
  Verify: `git grep -n "Draw exclusion" -- ui/src/components` prints the label.
- [x] 2.7 Make `usePlacing.ts` hold the limb and the exclusions beside the pairs, and extend `ui/src/composables/usePlacing.test.ts` with a test that they stay across steps.
  Verify: `npm --prefix ui run test -- src/composables/usePlacing.test.ts` passes.
- [x] 2.8 Hold the browser's types.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [x] 2.9 Hold the browser's unit tests.
  Verify: `uv run python -m tools.test_ui` exits 0.

## 3 — Bake

- [x] 3.1 **HALT CHECK** The tattoo edit's request, its numbering and its discard are built: its tests carry `edit_request` and `edit_discard`.
  Verify: `uv run pytest tests/test_edit.py tests/test_edit_session.py -k "edit_request or edit_discard"` passes.
- [x] 3.2 Add to `isekai/foundation/artifacts.py` `PLACEMENT_FILE` and `PlacementRecord`, and to `isekai/foundation/run.py` `placement_file` per [D5](design.md#d5); tests in `tests/test_edit_placement.py` carry `placement_names`.
  Verify: `uv run pytest tests/test_edit_placement.py -k placement_names` passes.
- [x] 3.3 Add to `isekai/pipeline/edit.py` `request_placed` per [D5](design.md#d5), sharing `request`'s body, the composite as bytes, the composite then the placement then the record written, a refusal writing nothing; tests carry `placement_request`.
  Verify: `uv run pytest tests/test_edit_placement.py -k placement_request` passes.
- [x] 3.4 Make `request_placed` refuse an edit image that is not on disk, naming that edit's wait, and record `places_on` per [D6](design.md#d6); tests carry `placement_chain`.
  Verify: `uv run pytest tests/test_edit_placement.py -k placement_chain` passes.
- [x] 3.5 Make the unread list of `isekai/interface/run_view.py` and the listings skip a placement record, and make the edit stage's discard and `discard_render` in `isekai/pipeline/generate.py` delete it with its edit; tests carry `placement_listing` and `placement_discard`, one in `tests/test_run_view.py`.
  Verify: `uv run pytest tests/test_edit_placement.py tests/test_run_view.py -k "placement_listing or placement_discard"` passes.
- [x] 3.6 Add to `tattoos.py` `Composite` and `composite` per [D5](design.md#d5): the layer over the whole render, Multiplied, as PNG bytes, and `values`, every field of the placement but `places_on` and the schema; tests carry `placement_composite` and hold that set.
  Verify: `uv run pytest tests/test_tattoo_placement.py -k placement_composite` passes.
- [x] 3.7 Add to `app.py` `POST /api/c/{collection}/tattoos/{name}/bake` per [D5](design.md#d5), calling `composite` and `request_placed` with the tracked edit `tattoo-wai` and the wiring's `rng`, and the route in the module's route table; tests in `tests/test_ui_placement.py` carry `placement_route_bake`, and `placement_route_guard` names the bake route among those the guard answers.
  Verify: `uv run pytest tests/test_ui_placement.py -k "placement_route_bake or placement_route_guard"` passes.
- [x] 3.8 Hold that `app.py` writes no file of its own and that the imports and layers hold.
  Verify: `uv run pytest tests/test_ui.py tests/test_pipeline_cli.py tests/test_layers.py` passes.
- [x] 3.9 Add `ui/src/review.ts` per [D8](design.md#d8): `summary` and `bakeState`; its tests in `ui/src/review.test.ts` bind through `spec`.
  Verify: `npm --prefix ui run test -- src/review.test.ts` passes.
- [x] 3.10 Add to `ui/src/api.ts` `export function bakeTattoo` and to `ui/src/types.ts` `Bake`.
  Verify: `git grep -n "export function bakeTattoo" ui/src/api.ts` prints it.
- [x] 3.11 Add `ui/src/components/ReviewBake.vue`, the review step: the image with the tattoo over it, the crop before and after, the summary from `summary`, a button back to each earlier stage, and *Bake*; show it in `ui/src/views/Place.vue` for the step `review`.
  Verify: `git grep -n "ReviewBake" -- ui/src/views` prints the use.
- [x] 3.12 Add the step `review` to the step set of `ui/src/routes.ts`, and a test in `ui/src/viewkey.test.ts` that it resolves to the `place` route.
  Verify: `npm --prefix ui run test -- src/viewkey.test.ts` passes.
- [x] 3.13 Hold the phase's tests under the acceptance's selector.
  Verify: `uv run pytest tests/test_tattoo_placement.py tests/test_edit_placement.py tests/test_ui_placement.py -k placement` passes.
- [x] 3.14 Hold the browser's types and unit tests.
  Verify: `uv run python -m tools.test_ui` exits 0.

## 4 — Leave

- [ ] 4.1 Add `ui/src/leave.ts` per [D8](design.md#d8): `lone`, `asks` and `left`; its tests in `ui/src/leave.test.ts` bind through `spec`.
  Verify: `npm --prefix ui run test -- src/leave.test.ts` passes.
- [ ] 4.2 Add `ui/src/components/LeaveDialog.vue`, a native dialog that closes on `esc`, and ask it from `ui/src/views/Place.vue` on a step change and on `onBeforeRouteLeave` while a stage holds a lone point.
  Verify: `git grep -n "LeaveDialog" -- ui/src/views` prints the use.
- [ ] 4.3 Make `ui/src/nokeys.test.ts` read the sources of every component the stages add, so none declares a command.
  Verify: `npm --prefix ui run test -- src/nokeys.test.ts` passes.
- [ ] 4.4 Hold the browser's types and unit tests.
  Verify: `uv run python -m tools.test_ui` exits 0.

## 5 — Docs

- [ ] 5.1 Add `### D53` to `docs/decisions.md` after D52 per [D12](design.md#d12): a placement is recorded beside its edit, the placement record, the held stage state, and that stage-1 pairs are the tattoo's.
  Verify: `git grep -n "### D53" docs/decisions.md` prints its heading.
- [ ] 5.2 Amend [D4](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children) in `docs/decisions.md` by one sentence: an edit request goes through the edit stage's own function.
  Verify: `git grep -n "through the edit stage" docs/decisions.md` prints the sentence.
- [ ] 5.3 In `ui/design/spec.md` extend §4's row for `…/place/<step>` with the steps `photo`, `render` and `review`.
  Verify: `git grep -n "place/<step>" ui/design/spec.md` prints the row.
- [ ] 5.4 In `ui/design/spec.md` add a row `**the placement**` to §10's table.
  Verify: `git grep -n "the placement\*\*" ui/design/spec.md` prints the row.
- [ ] 5.5 Extend the journey `### J9 · Place a tattoo` in `ui/design/spec.md` with the stages, the preview, the limb and exclusions, the review and the Leave dialog as built, state and refusals only.
  Verify: `git grep -n "Leave dialog" ui/design/spec.md` prints the line.
- [ ] 5.6 Add to the `## The app` section of `docs/edit-tattoo.md` the stages and the placement record, `<seed>.edit-<k>.placement.json`, what it holds and that a bake only queues a request; no path of the operator's notebook.
  Verify: `git grep -n "placement.json" -- docs` prints a line.
- [ ] 5.7 Name `place`, `preview`, `composite` and `request_placed` and their edges in `docs/modules.md`, `isekai/pipeline/README.md` and `isekai/shared/README.md`.
  Verify: `git grep -n "request_placed" isekai/pipeline/README.md` prints the line.
