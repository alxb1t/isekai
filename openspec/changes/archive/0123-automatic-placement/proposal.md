---
bump: minor
version: 0.83
after: [0122-the-placement]
---

# Automatic placement

The placement screen's stage 2 opens with the photograph-to-render pairs proposed from DWPose and SAM 2.1, run on the operator's machine, and the operator accepts or corrects them.

Reading map: [design](design.md) holds the models, the unpack, the pose, the segmenter, the pairs and the screen's state, [tasks](tasks.md) its phases, one of them a person's.

## Why

Placing a tattoo takes pairs for each stage, and the stage between the photograph and the render is the long one to click. A prototype showed that the pose of one arm, a silhouette of each bone and a bounded search for its edges give pairs the operator would only touch up, with an overlap of 0.83 and 0.78 against the operator's own clicks.

This change builds that into the screen as proposals. Nothing is applied: each pair is dashed until the operator accepts it or drags it, and forward waits for the last. The models are the declared runtime's ONNX files, so no package is added.

## What Changes

- New requirement, *Pairs are proposed from the pose and the silhouettes of the arm*: one `POST` with the render and the tattoo's points on the photograph, `{arm, pairs}`, kept nowhere.
- New requirement, *A person's pose is read from one box and one crop*: the detector's highest box, the estimator's crop grown by a quarter, the keypoints and their scores.
- New requirement, *A silhouette is segmented once an image and prompted once a bone*: the encoder once, the decoder for each bone.
- New requirement, *The models open on the CPU after their digests verify*: the declared runtime, the CPU provider alone, a refusal that names the fetch.
- New requirement, *A zip entry's members are unpacked and each verified*: `unpack` in a manifest entry, by declared destination alone.
- New requirement, *The placement models are one manifest, fetched by setup*: `config/placement.json`, `make setup`, `make drift`, CI's absent switch.
- New requirement, *Stage 2 proposes its pairs when it opens with none*: asked once, a spinner, a refusal with its fix.
- New requirement, *A proposed pair is accepted by a button or a drag*: *Accept*, *Accept all*, a dashed marker.
- New requirement, *Forward waits while a pair is proposed*: with its reason.
- D54 is new, the README names the estimator's training data, and the pins guide, the design spec and the modules are edited where they live.

## Capabilities

### New Capabilities

- `placement-proposal`: the proposal route, the pose, the segmenter and the models' opening.

### Modified Capabilities

- `model-provisioning`: the unpack of a zip entry and the placement manifest. Added requirements only.
- `ui`: stage 2's ask, its proposed pairs and forward's wait. Added requirements only.

## Impact

- New: `isekai/boundary/unpack.py`, `isekai/boundary/pose.py`, `isekai/boundary/sam2.py`, `isekai/shared/proposal.py`, `isekai/pipeline/proposing.py`, `tools/derive_placement.py`, `config/placement.json`, `ui/src/propose.ts`, and a test beside each module.
- Changed: `isekai/interface/wiring.py`, `isekai/interface/ui/app.py`, `tools/manifest.py`, `Makefile`, `.github/workflows/ci.yml`, `ui/src/types.ts`, `ui/src/api.ts`, `ui/src/pairs.ts`, `ui/src/composables/usePlacing.ts`, `ui/src/components/PairPanel.vue`, `ui/src/components/PairList.vue`, `ui/src/components/StageRender.vue`.
- Tests: `tests/test_provision_unpack.py`, `tests/test_derivation.py`, `tests/test_infra.py`, `tests/test_package_paths.py`, `tests/conftest.py`, `tests/test_placement_manifest.py`, `tests/test_pose.py`, `tests/test_sam2.py`, `tests/test_proposal.py`, `tests/test_propose.py`, `tests/test_ui_propose.py`, `tests/fakes.py`, and in `ui/src/` the tests of `pairs`, `propose`, `usePlacing` and `nokeys`.
- Docs: `docs/decisions.md`, `docs/pins.md`, `docs/edit-tattoo.md`, `docs/modules.md`, `ui/design/spec.md`, `README.md`, `isekai/boundary/README.md`, `isekai/shared/README.md`, `isekai/pipeline/README.md`.
- No dependency, no flow, no pinned digest of a flow, no format version and no end-to-end test changes. The models are a new manifest, fetched and never committed. `isekai/boundary/provision.py`, which the pod image copies, is unchanged, so no image is rebuilt.

## Not in this change

- Stage 1 made automatic, and the ink outline drawn automatically: not yet proven, and needed only when the source is a tattoo image.
- The direct stage, between a tattoo and a render: it has no photograph to find a pose in.
- Several people in one image: the highest-scoring box is the one person.
- A keypoint under the score cut proposes nothing for its bone: the operator clicks that bone.
- Keys, CoreML, a pod and browser tests: when the screen has been used and shows which are wanted.
