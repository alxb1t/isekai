# Automatic placement — tasks

The phases: the models and the unpack, a person's pins, the pose, the segmenter, the proposal, stage 2's proposed pairs, the docs. Phase 2 is a person's, and no phase spends money.

## Progress

- [x] 1 — Models · hard
- [ ] 2 — 🛑 **HUMAN** — the model pins
- [ ] 3 — Pose · hard
- [ ] 4 — Segment · hard
- [ ] 5 — Proposal · hard
- [ ] 6 — Stage 2 · moderate
- [ ] 7 — Docs · moderate

## 1 — Models

- [x] 1.1 Add `isekai/boundary/unpack.py`, a new module, with `PLACEMENT_MANIFEST_PATH`, `PLACEMENT_REMEDY` (its fetch command), `Member` and `ZipEntry`, `provision.Entry` with the optional `unpack`,
  per [D3](design.md#d3) and [D4](design.md#d4); add the path's anchor to `tests/test_package_paths.py`. `isekai/boundary/provision.py` is not edited by any task.
  Verify: `uv run pytest tests/test_package_paths.py -k PLACEMENT_MANIFEST_PATH` passes.
- [x] 1.2 Add to `unpack.py` `unpack_members(entry, archive, models_dir)` per [D4](design.md#d4); tests in `tests/test_provision_unpack.py` carry `unpack_lands`,
  `unpack_names`, `unpack_digest`, `unpack_size` and `unpack_missing`.
  Verify: `uv run pytest tests/test_provision_unpack.py -k "unpack_lands or unpack_names or unpack_digest or unpack_size or unpack_missing"` passes.
- [x] 1.3 Add to `unpack.py` `fetch` and the `fetch` verb of `python -m isekai.boundary.unpack`: it decides each declared member's destination before a transfer, lands the entries through
  `provision.fetch`, and unpacks after an entry lands, and after it is skipped, per [D4](design.md#d4); tests carry `unpack_gone` and `unpack_stop`.
  Verify: `uv run pytest tests/test_provision_unpack.py -k "unpack_gone or unpack_stop"` passes.
- [x] 1.4 Add to `unpack.py` `member_for` and `resolve_member` per [D4](design.md#d4); tests carry `unpack_resolve`.
  Verify: `uv run pytest tests/test_provision_unpack.py -k unpack_resolve` passes.
- [x] 1.5 Hold that the entry point's import graph reaches no wheel and the layers hold.
  Verify: `uv run pytest tests/test_pipeline_cli.py tests/test_layers.py` passes.
- [x] 1.6 Give `tools/manifest.py` the optional `unpack` of `ManifestEntry` and `Spec`, and `members_of`, per [D5](design.md#d5); tests in `tests/test_derivation.py`
  carry `derive_unpack` over a fake download.
  Verify: `uv run pytest tests/test_derivation.py -k derive_unpack` passes.
- [x] 1.7 Add `tools/derive_placement.py` per [D3](design.md#d3) and [D5](design.md#d5): `PINNED` 2026-11-11, `PUBLISHERS` `yzd-v` and `vietanhdev`, a spec for each file
  of the table, and `main` writing `PLACEMENT_MANIFEST_PATH`; add it to the derivers `tests/test_derivation.py` lists, with tests carrying `derive_placement`.
  Verify: `uv run pytest tests/test_derivation.py -k derive_placement` passes.
- [x] 1.8 Edit `Makefile` per [D3](design.md#d3): `setup` fetches `config/placement.json` after the vocabulary, and `drift` runs the deriver directly after `tools.derive_reader`. The `gate` recipe
  keeps its lines, and `make -n gate` prints what it did. `Makefile` changes by exactly these lines:
  ```diff
  - # Chromium and the vocabulary. Not part of the gate, which never fetches.
  + # Chromium, the vocabulary and the placement models. Not part of the gate, which never fetches.
  +     uv run python -m isekai.boundary.unpack fetch config/placement.json
  +     uv run python -m tools.derive_placement
  ```
  Verify: `grep -c "placement" Makefile` prints `3`.
- [x] 1.9 Add `ISEKAI_PLACEMENT: absent` to the `env` of the gate step and of the browser-test step in `.github/workflows/ci.yml`; tests in
  `tests/test_infra.py` carry `infra_placement`: `setup` fetches the manifest, `drift` derives it, `gate` names neither, each CI step declares it absent.
  Verify: `uv run pytest tests/test_infra.py -k infra_placement` passes.
- [x] 1.10 Hold that the pod image's record agrees with the tree per [D4](design.md#d4): `isekai/boundary/provision.py` is as the image holds it, and `config/image.json` is not edited.
  Verify: `uv run pytest tests/test_infra.py -k build_record_agrees` passes.

## 2 — 🛑 **HUMAN** — the model pins

- [ ] 2.1 From this worktree's root, on a machine that reaches `huggingface.co`, run `uv run python -m tools.derive_placement`. It writes `config/placement.json`.
  Verify: `ls config/placement.json` prints the path.
- [ ] 2.2 In the same worktree run `uv run python -m isekai.boundary.unpack fetch config/placement.json`. It lands the detector, the estimator and the archive, and unpacks the archive into `models/sam2/`.
  Verify: `ls models/dwpose/yolox_l.onnx models/dwpose/dw-ll_ucoco_384.onnx models/sam2/encoder.onnx models/sam2/decoder.onnx` prints each path.
- [ ] 2.3 Read the manifest: the detector's digest is the pod's pin, `7860ae79de6c89a3c1eb72ae9a2756c0ccfbe04b7791bb5880afabd97855a411`, as the render manifest has it.
  Verify: `grep -c 7860ae79de6c89a3c1eb72ae9a2756c0ccfbe04b7791bb5880afabd97855a411 config/placement.json` prints `1`.

## 3 — Pose

- [ ] 3.1 Add to `tests/conftest.py` `require_placement(path)` after `require_vocabulary`: it returns when the file exists, skips under `ISEKAI_PLACEMENT=absent`, and else fails
  naming `PLACEMENT_REMEDY`; its tests in `tests/test_placement_manifest.py` carry `placement_require`.
  Verify: `uv run pytest tests/test_placement_manifest.py -k placement_require` passes.
- [ ] 3.2 Add to `tests/test_placement_manifest.py` the tests of the real manifest per [D3](design.md#d3): `placement_pins` for each source and digest, `placement_detector` for the
  detector's equality with the pod's pin, `placement_members` for the archive's encoder and decoder.
  Verify: `uv run pytest tests/test_placement_manifest.py -k "placement_pins or placement_detector or placement_members"` passes.
- [ ] 3.3 Add `isekai/boundary/pose.py` with `Pose`, `PoseFinder` and `verified_paths(models_dir)` per [D6](design.md#d6): the detector and the estimator through
  `provision.resolve`, an absent file refused naming `PLACEMENT_REMEDY`; tests in `tests/test_pose.py` carry `pose_verified`.
  Verify: `uv run pytest tests/test_pose.py -k pose_verified` passes.
- [ ] 3.4 Add to `pose.py` `fit` and `person_box` per [D6](design.md#d6): the image fitted into the detector's square input and padded, the output rows decoded on their strides, the
  highest objectness times person score the box; tests carry `pose_box`.
  Verify: `uv run pytest tests/test_pose.py -k pose_box` passes.
- [ ] 3.5 Add to `pose.py` `crop_for` and `read_keypoints` per [D6](design.md#d6): the box grown by a quarter, held to the estimator's aspect and scaled, the highest value on each
  axis divided by the split ratio and mapped back, the score the lower of the two; tests carry `pose_keypoints`.
  Verify: `uv run pytest tests/test_pose.py -k pose_keypoints` passes.
- [ ] 3.6 Add to `pose.py` `OnnxPoseFinder` and `open_pose(models_dir)` per [D2](design.md#d2) and [D6](design.md#d6): `onnxruntime`, numpy and Pillow imported inside, each session on
  the CPU provider alone, `find` returning a `Pose`, and none when the detector finds no person; tests over a recording runtime carry `pose_find` and `pose_cpu`.
  Verify: `uv run pytest tests/test_pose.py -k "pose_find or pose_cpu"` passes.
- [ ] 3.7 Add to `tests/test_pose.py` `pose_real`: through `require_placement`, it opens the real finder over the provisioned files, reads a synthetic image, and holds that
  the body points and their scores are finite and of one length.
  Verify: `uv run pytest tests/test_pose.py -k pose_real` passes.
- [ ] 3.8 Hold that the entry point's import graph reaches no wheel and the layers hold.
  Verify: `uv run pytest tests/test_pipeline_cli.py tests/test_layers.py` passes.

## 4 — Segment

- [ ] 4.1 **HALT CHECK** The encoder answers the names [D7](design.md#d7) expects.
  Verify: `uv run python -c "import onnxruntime; print([o.name for o in onnxruntime.InferenceSession('models/sam2/encoder.onnx').get_outputs()])"` prints a list holding `image_embed`, `high_res_feats_0` and `high_res_feats_1`.
- [ ] 4.2 **HALT CHECK** The decoder takes and answers the names [D7](design.md#d7) expects.
  Verify: `uv run python -c "import onnxruntime; s = onnxruntime.InferenceSession('models/sam2/decoder.onnx'); print([i.name for i in s.get_inputs()], [o.name for o in s.get_outputs()])"` prints the inputs `image_embed`, `high_res_feats_0`, `high_res_feats_1`, `point_coords`, `point_labels`, `mask_input` and `has_mask_input`, and the output `masks`.
- [ ] 4.3 Add `isekai/boundary/sam2.py` with `prepare(image)` per [D7](design.md#d7): the image resized bilinear to the encoder's square, normalised by the ImageNet mean and deviation,
  channels first, numpy and Pillow imported inside; tests in `tests/test_sam2.py` carry `sam_prepare`.
  Verify: `uv run pytest tests/test_sam2.py -k sam_prepare` passes.
- [ ] 4.4 Add to `sam2.py` `Segmenter`, `Embedding` and `OnnxSegmenter.embed` per [D7](design.md#d7): the encoder run once an image, its features and the image's size kept;
  tests over a recording session carry `sam_embed`.
  Verify: `uv run pytest tests/test_sam2.py -k sam_embed` passes.
- [ ] 4.5 Add to `sam2.py` `Embedding.mask(positive, negative)` per [D7](design.md#d7): the points scaled to the input and labelled 1 and 0, every input the decoder declares given
  from the table of known names, one without a value refused by name, the mask the logits above 0 at the image's size; tests carry `sam_prompt` and `sam_inputs`.
  Verify: `uv run pytest tests/test_sam2.py -k "sam_prompt or sam_inputs"` passes.
- [ ] 4.6 Add to `sam2.py` `open_segmenter(models_dir)` per [D2](design.md#d2): the encoder and decoder through `unpack.resolve_member`, each session on the CPU provider alone, an absent file
  refused naming `PLACEMENT_REMEDY`; tests carry `sam_open`.
  Verify: `uv run pytest tests/test_sam2.py -k sam_open` passes.
- [ ] 4.7 Add to `tests/test_sam2.py` `sam_real`: through `require_placement`, it opens the real segmenter, embeds a synthetic image, prompts a point, and holds that the mask is a boolean
  array of the image's size.
  Verify: `uv run pytest tests/test_sam2.py -k sam_real` passes.
- [ ] 4.8 Hold that the entry point's import graph reaches no wheel and the layers hold.
  Verify: `uv run pytest tests/test_pipeline_cli.py tests/test_layers.py` passes.

## 5 — Proposal

- [ ] 5.1 **HALT CHECK** 0122's preview route is built: its tests carry `placement_route_preview`.
  Verify: `grep -n "placement_route_preview" tests/test_ui_placement.py` prints it.
- [ ] 5.2 **HALT CHECK** The photograph the preview reads is the upright one.
  Verify: `grep -n -e "exif_transpose" -e "upright" isekai/pipeline/tattoos.py` prints the use.
- [ ] 5.3 Add `isekai/shared/proposal.py` per [D8](design.md#d8): the constants, `usable_bone`, `prompt_points`, and `edge_pair(mask, centre, normal, reach, luminance)` bounded by the band
  and, with a luminance, by the first dark line past `DARK_AFTER`; numpy imported inside; tests in `tests/test_proposal.py` carry `propose_edges`.
  Verify: `uv run pytest tests/test_proposal.py -k propose_edges` passes.
- [ ] 5.4 Add to `proposal.py` `bone_pairs` and `joint_pairs` per [D8](design.md#d8): the order of bones, fractions and edges, the keypoint cut on each bone and joint; tests carry `propose_pairs`.
  Verify: `uv run pytest tests/test_proposal.py -k propose_pairs` passes.
- [ ] 5.5 Add to `proposal.py` `nearest_side` per [D9](design.md#d9): the mean of the points against each usable arm's polyline in the photograph, the left on a tie; tests carry `propose_side`.
  Verify: `uv run pytest tests/test_proposal.py -k propose_side` passes.
- [ ] 5.6 Add `isekai/pipeline/proposing.py` with `Proposal`, `Proposer` and `propose` per [D10](design.md#d10), an answer with no pair for no person, and for no usable bone; add `FakePoseFinder`
  and `FakeSegmenter` to `tests/fakes.py`; tests in `tests/test_propose.py` carry `propose_pipeline`.
  Verify: `uv run pytest tests/test_propose.py -k propose_pipeline` passes.
- [ ] 5.7 Add to `isekai/interface/wiring.py` the `proposer` thunk of `Wiring`, `None` by default, and the cached `proposer_for`, set by `wiring_from`, per [D10](design.md#d10);
  tests in `tests/test_propose.py` carry `propose_wiring`: the models opened once, a wiring with none refused.
  Verify: `uv run pytest tests/test_propose.py -k propose_wiring` passes.
- [ ] 5.8 Add to `isekai/interface/ui/app.py` `POST /api/c/{collection}/place/propose` per [D10](design.md#d10): the body `{digest, flow, version, seed, points}` checked, the photograph and the render
  read as the preview route reads them, `{arm, pairs}` answered `no-store`, and the route in the module's table; tests in `tests/test_ui_propose.py` carry `propose_route`.
  Verify: `uv run pytest tests/test_ui_propose.py -k propose_route` passes.
- [ ] 5.9 Hold that the guard answers the new route and `app.py` writes no file of its own; tests carry `propose_guard`.
  Verify: `uv run pytest tests/test_ui_propose.py tests/test_ui.py -k "propose_guard or invariant"` passes.
- [ ] 5.10 Hold that the entry point's import graph reaches no wheel and the layers hold.
  Verify: `uv run pytest tests/test_pipeline_cli.py tests/test_layers.py` passes.
- [ ] 5.11 Hold the phase's tests under the acceptance's selector.
  Verify: `uv run pytest tests/test_pose.py tests/test_sam2.py tests/test_propose.py tests/test_ui_propose.py -k "pose or sam or propose"` passes.

## 6 — Stage 2

- [ ] 6.1 **HALT CHECK** 0122's editor, render stage and placing state are built.
  Verify: `ls ui/src/pairs.ts ui/src/components/StageRender.vue ui/src/components/PairPanel.vue ui/src/components/PairList.vue ui/src/composables/usePlacing.ts` prints each path.
- [ ] 6.2 **HALT CHECK** `Pair` is an object that holds its number and its point on each image, as [D11](design.md#d11) takes it.
  Verify: `grep -n -e "interface Pair" -e "type Pair" ui/src/types.ts` prints its declaration.
- [ ] 6.3 Add to `ui/src/types.ts` the key `proposed` of `Pair` and `Proposal`, and to `ui/src/api.ts` `export function proposePairs`, which posts the body of [D10](design.md#d10).
  Verify: `git grep -n "export function proposePairs" ui/src/api.ts` prints it.
- [ ] 6.4 Add to `ui/src/pairs.ts` per [D11](design.md#d11) `arrived`, `accepted`, `export function acceptedAll`, `proposals` and `sent`, `arrived` written into every snapshot of the history; make `moved` clear
  `proposed` of the pair it moves and `forward` wait while a pair is proposed; its tests in `ui/src/pairs.test.ts` bind through `spec`.
  Verify: `grep -n "export function acceptedAll" ui/src/pairs.ts` prints it.
- [ ] 6.5 Add `ui/src/propose.ts` per [D12](design.md#d12): `due`, `asked`, `answered`, `refused`, `view` and `pointsOf`; its tests in `ui/src/propose.test.ts` bind through `spec`.
  Verify: `npm --prefix ui run test -- src/propose.test.ts` passes.
- [ ] 6.6 Make `ui/src/composables/usePlacing.ts` hold `proposalAsked`, keyed by tattoo and render, per [D12](design.md#d12); its tests in `ui/src/composables/usePlacing.test.ts`
  hold that it stays across steps and that a second opening asks nothing.
  Verify: `grep -n "proposalAsked" ui/src/composables/usePlacing.ts` prints the use.
- [ ] 6.7 Draw a proposed point with a dashed ring in `ui/src/components/PairPanel.vue` per [D11](design.md#d11).
  Verify: `grep -n "proposed" ui/src/components/PairPanel.vue` prints the use.
- [ ] 6.8 Mark a proposed pair's row in `ui/src/components/PairList.vue` per [D11](design.md#d11).
  Verify: `grep -n "proposed" ui/src/components/PairList.vue` prints the use.
- [ ] 6.9 Make `ui/src/components/StageRender.vue` ask through `proposePairs` when `due`, sending `pointsOf`, show the line of `view`, offer *Accept* and *Accept all*, and send the preview's pairs through `sent`.
  Verify: `grep -n "Accept all" ui/src/components/StageRender.vue` prints the label.
- [ ] 6.10 Hold that no changed component declares a key.
  Verify: `npm --prefix ui run test -- src/nokeys.test.ts` passes.
- [ ] 6.11 Hold the browser's types.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 6.12 Hold the browser's unit tests.
  Verify: `uv run python -m tools.test_ui` exits 0.

## 7 — Docs

- [ ] 7.1 **HALT CHECK** 0122's decision D53 stands on the decisions page.
  Verify: `git grep -n "### D53" docs/decisions.md` prints its heading.
- [ ] 7.2 Add `### D54` to `docs/decisions.md` after D53 per [D14](design.md#d14): automatic pairs run on the operator's machine, from pinned files, and are kept nowhere; its `Made by` is `0123`.
  Verify: `git grep -n "### D54" docs/decisions.md` prints its heading.
- [ ] 7.3 Add to the `## License` section of `README.md` the sentence of [D13](design.md#d13): the pose estimator's COCO-WholeBody training data is CC BY-NC 4.0, and the automatic pairs are for non-commercial use.
  Verify: `git grep -n "COCO-WholeBody" README.md` prints the line.
- [ ] 7.4 In `docs/pins.md` add a row for `config/placement.json` to the inventory and `tools/derive_placement.py` to *A model manifest*.
  Verify: `git grep -n "config/placement.json" docs/pins.md` prints the row.
- [ ] 7.5 In `ui/design/spec.md` extend the journey `### J9 · Place a tattoo` with the proposed state: the spinner, the refusal, *Accept*, *Accept all*, the dashed marker and forward's wait, state and refusals only.
  Verify: `git grep -n "Accept all" ui/design/spec.md` prints the line.
- [ ] 7.6 In `ui/design/spec.md` add a row `**automatic placement**` to §10's table.
  Verify: `git grep -n "automatic placement\*\*" ui/design/spec.md` prints the row.
- [ ] 7.7 Add to the `## The app` section of `docs/edit-tattoo.md` the proposed pairs of stage 2: what proposes them, that nothing is kept, and the fetch; no path of the operator's notebook.
  Verify: `grep -n "proposed pairs" docs/edit-tattoo.md` prints a line.
- [ ] 7.8 Name `unpack`, `pose`, `sam2`, `proposal` and `proposing` and their edges in `docs/modules.md`, `isekai/boundary/README.md`, `isekai/shared/README.md` and `isekai/pipeline/README.md`.
  Verify: `git grep -n "proposing" isekai/pipeline/README.md` prints the line.
