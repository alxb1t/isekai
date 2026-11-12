# Automatic placement — design

Stage 2 of the placement screen gains proposed pairs: DWPose and SAM 2.1 run on the operator's machine through the declared runtime, and the operator accepts or corrects what they propose. Verdict: ready to build, in the phases of [tasks](tasks.md), with a person's phase for the model pins.

## Context

The placement screen of 0122 takes photograph-to-render pairs by clicks, and 0121 and 0122 left automatic pairs to this version. A prototype proved that the pose of one arm, a silhouette of each bone and a bounded search for its edges give pairs the operator would only touch up.

```
④ opens, no pair ─▶ POST /api/c/<collection>/place/propose   {digest, flow, version, seed, points}
                       │ the photograph and the render, read as the preview reads them
                       ▼
   pose     detector ─▶ one person's box ─▶ estimator ─▶ 17 keypoints and scores   (each image)
   arm      the arm whose bones lie nearest `points` in the photograph
   segment  encoder once an image ─▶ decoder once a bone                           (each image)
   pairs    at each fraction of a bone: two edges and the middle; then the joints  (numpy)
                       ▼
   {arm, pairs: [[[ax, ay], [bx, by]], …]}  ─▶ held by the page as proposed ─▶ Accept, or a drag
```

The build runs stacked on 0122's, which runs on the core's and the tattoo edit's. It uses 0122's pairs editor, render stage and server helpers, and the models are the tagger's precedent: one manifest, fetched by setup, verified before a session opens ([D20](../../../docs/decisions.md#d20--the-entry-point-loads-no-third-party-package), [D22](../../../docs/decisions.md#d22--dependencies-are-declared-and-pinned)).

## Goals / Non-Goals

- **Goals:** the placement manifest and its deriver; a zip entry unpacked by `unpack`, a module the pod image does not copy; the pose and segmenter seams over the declared runtime; the pairs as numpy functions; the propose route; proposed pairs on stage 2 with *Accept* and *Accept all*; the decision and the docs.
- **Non-Goals:** stage 1 and the ink outline made automatic, the direct stage, several people in one image, a second runtime or CoreML, a keyboard, a draft file, a browser test, a pod. See the proposal's *Not in this change*.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the proposal is stage 2 only, for a two-stage tattoo and a cut | only stage 2 is proven, against the operator's clicks | stage 1 by optimisation; the direct stage |
| [D2](#d2) | the models run through the declared `onnxruntime`, `numpy` and `Pillow`, on the CPU, and no package is added | SAM 2.1 small as ONNX gave the PyTorch mask exactly | torch on MPS; CoreML; OpenCV |
| [D3](#d3) | the files are pinned in `config/placement.json`, fetched by `make setup` | the tagger's precedent: the gate never fetches | one section of `config/models.json` |
| [D4](#d4) | a zip entry declares its members, and `isekai/boundary/unpack.py` unpacks each by its declared destination; `provision.py` is unchanged | the archive's own names must decide nothing, and the pod image copies `provision.py` | extracting by the archive's names; the archive loaded in place; the unpack in `provision.py`, which is an image rebuild |
| [D5](#d5) | a deriver writes the manifest, and a person runs it in phase 2 | the cut and the run cannot reach the model host | digests written from memory |
| [D6](#d6) | the pose is the detector's highest-scoring box and the estimator's crop of it, read as the prototype read it | the prototype's pose held on both images | a person-score floor; non-maximum suppression |
| [D7](#d7) | the segmenter embeds an image once and prompts a bone once | the encoder costs seconds and the decoder milliseconds | one encode a bone |
| [D8](#d8) | the pairs are numpy functions of masks and keypoints, at fixed fractions, bounded by a band and the render's first dark line | the prototype's fix took the bent arm from 0.61 to 0.78 | the mask's own silhouette edge |
| [D9](#d9) | the arm proposed is the one nearest the tattoo's points on the photograph | ④ opens with no click, and one arm is one warp | both arms; a side chosen by hand |
| [D10](#d10) | the route answers in the server's process through a `proposer` seam, and keeps nothing | a proposal is no stage and no artifact | a child process; a saved proposal |
| [D11](#d11) | a pair carries `proposed`; a button or a drag accepts it; forward waits for none | the handoff's state, with no keys | keys; a separate list |
| [D12](#d12) | stage 2 asks once, when it opens with no pair, and shows a spinner or a refusal | the screen's clicks must keep working | asking on every open |
| [D13](#d13) | DWPose's non-commercial training data is accepted and one README line names it | a personal, non-commercial project | a licensed estimator |
| [D14](#d14) | D54 is the decision, and the docs are edited where they live | 0122's design takes D53 | D53 |

### D1

- The proposal is the photograph-to-render pairs of the stage 2 of a two-stage tattoo and of a cut. Stage 1, the direct stage and the ink outline stay clicked.
- The prototype's overlap against the operator's clicked decal was 0.83 and 0.78 on its sleeve cases, each needing corrections. That is why the pairs are proposed, never applied.

### D2

- `isekai/boundary/pose.py` and `isekai/boundary/sam2.py` import `onnxruntime`, `numpy` and `Pillow` inside the functions that use them, as `wd14.py` does, so `python -m isekai` reaches none.
- Each session is made with `providers=["CPUExecutionProvider"]`. The research measured CoreML faster for pose and slower for SAM, with a slow first compile; one provider keeps one behaviour.
- The pose crop is a Pillow affine transform, the preprocessing a Pillow resize and numpy. Channels are RGB as Pillow reads them; the research scored RGB and BGR alike.

### D3

`config/placement.json` has the shape of the other manifests, `pinned`, `publishers`, `entries`, with `yzd-v` and `vietanhdev` as publishers: each serves a file from its own repository.

| dest | source | role |
|---|---|---|
| `dwpose/yolox_l.onnx` | `yzd-v/DWPose` at `1a7144101628d69ee7a3768d1ee3a094070dc388` | the detector, the pod's own pin |
| `dwpose/dw-ll_ucoco_384.onnx` | the same repository and revision | the estimator |
| `sam2/sam2.1_hiera_small_20260221.zip` | `vietanhdev/segment-anything-2.1-onnx-models` at `6a3ac868340a3196a349050a6efae22a5acc0330` | the archive |
| `sam2/encoder.onnx`, `sam2/decoder.onnx` | members of the archive | the segmenter |

- `unpack.PLACEMENT_MANIFEST_PATH` names the file, and `unpack.PLACEMENT_REMEDY` is its fetch, `uv run python -m isekai.boundary.unpack fetch config/placement.json`. `make setup` fetches it, `make drift` re-derives it, and CI declares it absent through `ISEKAI_PLACEMENT: absent`, as `ISEKAI_VOCABULARY` is.
- The alternative, `onnx-community/sam2.1-hiera-small-ONNX`, has no licence field and no README; the chosen export is Apache-2.0 weights under an MIT exporter.

### D4

- The unpack is `isekai/boundary/unpack.py`, and `isekai/boundary/provision.py` does not change. The `Dockerfile` copies `provision.py` into the pod image and `config/image.json` records its digest ([D28](../../../docs/decisions.md#d28--the-image-carries-code-the-volume-carries-weights), `docs/pins.md`), so an edit to it is an image rebuild, a push and a pod; these models never reach a pod.
- `unpack.Member` is `{member, dest, sha256, bytes}`, and `unpack.ZipEntry` is `provision.Entry` with `unpack`, optional: a list of members. `provision.Entry` and `ENTRY_KEYS` are unchanged, and `provision.fetch` reads no key it does not name, so it lands an archive as it lands any file.
- `unpack.fetch(manifest, models_dir, fetcher, wait)` decides each member's destination before any transfer: a member present with other bytes aborts, left where it is, and no entry is asked for. It then lands the entries through `provision.fetch`, and after the archive lands or is skipped, each absent member is read from it by the declared `member` name, written to `dest.partial` and renamed once its digest verifies.
- `python -m isekai.boundary.unpack fetch [--models-dir DIR] [manifest]` is that `fetch` over `provision.HuggingFaceFetcher`, the manifest defaulting to the placement's. `provision`'s own command line still lands the entries of any manifest and unpacks nothing.
- The read is capped at the declared size plus one byte, and a name in the archive is never joined onto a path. The archive stays, so a gone member is unpacked with no transfer.
- `unpack.member_for(manifest, dest)` and `unpack.resolve_member(dest, models_dir, manifest)` are `provision.entry_for` and `provision.resolve` for a member: the archive's sources must be pinned, the destination resolves through `provision.resolve_dest`, and the member's digest verifies. The detector and the estimator are plain entries and resolve through `provision.resolve`.

### D5

- `tools/derive_placement.py` follows the other derivers: its spec names the sources, `tools/manifest.py` digests them, and `write` writes the file. The archive's digest is its published LFS id; each member's digest and size are read from the archive, which `members_of(source, sha256, wanted)` streams once to a file in a temporary directory with `urllib.request.urlopen`, as the digest functions fetch, and hashes against the published id first.
- The tests fake `urllib.request.urlopen` with a response of their own in `tests/test_derivation.py`, one whose `read(n)` and `read()` run to the end of a small zip; the digest tests' double does not advance and is not reused.
- The deriver finds a member by a name suffix, `encoder.onnx` and `decoder.onnx`, and refuses none or several.
- Phase 2 is a person's. The run's network is its package hosts, and no digest of the estimator, the archive or its members is known to the cut. The detector's digest is the pod's, and the manifest's check that they are equal holds the rest.

### D6

- The detector reads the image fitted into its square input, the aspect kept, the rest padded with grey 114. Its output rows are decoded on strides 8, 16 and 32, and the one row with the highest objectness times person score is the person, with no suppression.
- The estimator reads a crop of that box grown by a quarter, held to the input's aspect and scaled to the input size, normalised by the declared mean and deviation. A keypoint is the position of the highest value on each axis divided by the split ratio, mapped back by the crop; its score is the lower of those highest values.
- `Pose` holds the box, the body points and their scores in COCO order. `PoseFinder.find(image)` returns a `Pose`, or none when the detector answers no row.

### D7

- The encoder takes the image resized to 1024 by 1024, bilinear, normalised by the ImageNet mean and deviation, channels first. `embed(image)` runs it once and returns an `Embedding` holding the features and the image's size.
- `Embedding.mask(positive, negative)` scales the points to the input, labels them 1 and 0, and runs the decoder. The decoder is given every input it declares from a table of known names and refuses, naming it, one the table lacks. The mask is the logit map above 0, at the image's size.
- The expected names are samexporter's: the encoder answers `image_embed`, `high_res_feats_0` and `high_res_feats_1`; the decoder takes them with `point_coords`, `point_labels`, `mask_input` and `has_mask_input`, and answers `masks`. Phase 4's first task checks them against the unpacked files.

### D8

`isekai/shared/proposal.py` holds the geometry, numpy imported inside, with these constants:

| constant | value | meaning |
|---|---|---|
| `SCORE_CUT` | 0.3 | a keypoint under it proposes nothing for its bone or joint |
| `PROMPTS` | 0.25, 0.5, 0.75 | positive points along the bone |
| `STEPS` | 6 | fractions along each bone, evenly from 0.1 to 0.9, where edges are searched |
| `BAND` | 0.3 | the furthest an edge may lie from the bone, as a fraction of its length |
| `DARK` | 0.42 | the render's luminance below which a line stops an edge |
| `DARK_AFTER` | 3 | pixels from the bone within which a dark line stops nothing, as the bone's own line may be dark |

- A bone is usable when both its keypoints score at least `SCORE_CUT` in both images. A joint is usable when its keypoint does in both.
- A bone's negatives are the other bone's middle, when that bone is usable, and the torso, the mean of the shoulders and hips that score at least the cut.
- At a fraction `t`, the search walks the line through the point `t` along the bone, across it, to each side, one pixel at a time from the bone, until the mask ends, `BAND` of the bone's length is reached, or in the render, past `DARK_AFTER`, the luminance is under `DARK`. The edge is the last pixel kept, and the search gives no edge when the first pixel is not kept. It proposes the last point on each side and their middle. A fraction where either image has no edge on both sides proposes nothing.
- The order is each usable bone in turn, upper arm then forearm, at each fraction the first edge, the second edge and the middle; then the shoulder, the elbow and the wrist.

### D9

- The points the page sends are the tattoo's on the photograph. `nearest_side` takes their mean, and for each arm with a usable bone in both images the distance from that mean to the arm's polyline, shoulder to elbow to wrist, in the photograph. The smaller distance wins, the left on a tie.
- No arm usable, no person in either image or no pair gives an answer with no pair, never a refusal.

### D10

| module | layer | holds |
|---|---|---|
| `isekai/boundary/pose.py` | boundary | `Pose`, `PoseFinder`, `OnnxPoseFinder`, `verified_paths`, `open_pose` |
| `isekai/boundary/sam2.py` | boundary | `Segmenter`, `Embedding`, `OnnxSegmenter`, `open_segmenter` |
| `isekai/shared/proposal.py` | shared | the geometry of [D8](#d8) and [D9](#d9) |
| `isekai/pipeline/proposing.py` | pipeline | `Proposal`, `Proposer`, `propose` |
| `isekai/interface/wiring.py` | interface | the `proposer` seam and `proposer_for` |
| `isekai/interface/ui/app.py` | interface | `POST /api/c/<collection>/place/propose` |

- `propose(photograph, render, points, pose, segmenter)` returns `Proposal(arm, pairs)` and reads no file. `photograph` and `render` are RGB Pillow images, typed under `TYPE_CHECKING` as `isekai/shared/image.py` types its images; the route opens them the way the preview route does, upright.
- `propose` makes the render's luminance, its grey scaled to 0 to 1, once, and passes it to the edge search; the seams take the images and return arrays, and no seam names a Pillow type at module scope.
- `Wiring.proposer` is a thunk, `None` by default; `proposer_for` is cached, so the sessions open on the first ask and stay open. A wiring with none refuses the route, saying so.
- The route is a plain function and runs in the threadpool. It answers `{arm, pairs}`, `no-store`, and writes nothing. It is no stage and no artifact, so [D4](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children) is not engaged.

### D11

- `Pair` in `ui/src/types.ts` is an object holding its number and its two points, and gains `proposed`, absent for an ordinary pair. `pairs.ts` gains `arrived`, which appends the answer's pairs as proposed after the held ones; `accepted` and `acceptedAll`; `proposals`, the proposed pairs; `sent`, the complete pairs as `[[ax, ay], [bx, by]]`; and `moved` clears `proposed` of the pair it moves.
- The preview takes the proposed pairs with the ordinary ones, so the operator sees the proposal warped, and `sent` gives the server a pair with no `proposed` key. The bake cannot hold a proposed pair, as forward waits for none. `arrived` is no step of the history and is written into every snapshot of it, so undo removes the operator's own changes, even one made while the ask was pending, and never the proposal.
- `forward` waits while a pair is proposed, saying `<n> proposed · accept or delete them`, before the floor and the lone point. Undo and delete are the editor's own.
- `PairPanel.vue` draws a proposed point with a dashed ring in `--point-ring`, `PairList.vue` marks its row, and the buttons are in `StageRender.vue`. No component declares a key.

### D12

- `ui/src/propose.ts` holds the ask's state: `due`, `asked`, `answered`, `refused`, `view` and `pointsOf`. `due` is true for stage 2 of a two-stage tattoo or a cut, with no pair held and no ask recorded for that tattoo and render.
- `pointsOf(stage1, outline)` gives the points sent: the photograph side of the stage-1 pairs, or a cut's outline.
- `usePlacing.ts` holds the state as `proposalAsked`, keyed by tattoo and render, so a step change keeps it and a second opening asks nothing. A reload loses the held pairs and the ask's record, so the next opening asks again. Leaving a stage asks only for a lone point, as the Leave dialog does, and a proposed pair is no lone point.
- `view` is *Proposing pairs…* while asked, the refusal's words after a refusal, and *Nothing proposed — place the pairs by clicking* after an empty answer.

### D13

README's `## License` section gains one sentence: the placement screen's pose estimator was trained on COCO-WholeBody, whose annotations are CC BY-NC 4.0, and the automatic pairs are for non-commercial use. Whether that binds the weights is unsettled, and the pod already runs DWPose for the flows.

### D14

- `docs/decisions.md` gets D54, automatic pairs run on the operator's machine, from pinned files, and are kept nowhere. It names D53 as 0122's, and `Made by` is `0123`.
- `ui/design/spec.md` gets the proposed state in J9 and a row in §10; `docs/pins.md`, `docs/edit-tattoo.md`, `docs/modules.md`, the group READMEs and the README are edited where they live. The brief's acceptance names D53; the heading to find is D54.

## Tests

Tests sit at the lowest layer that can fail: the unpack over a small zip in a temporary directory, the pose and segmenter over recording sessions, the geometry over synthetic masks, the route over the test client, and the editor and the ask's state as plain TypeScript. The checks that read the real models skip under `ISEKAI_PLACEMENT=absent`.

Every new test carries its `spec` marker. No test boots a browser, and the end-to-end suite gains none: `git diff --name-only main -- tests/e2e` prints nothing at the release.

| file | layer | holds |
|---|---|---|
| `tests/test_provision_unpack.py` | unit | `unpack`, the fetch order, `member_for`, `resolve_member` |
| `tests/test_derivation.py` | unit | the new deriver and its member digests |
| `tests/test_infra.py` | unit | setup, drift and CI carry the manifest; the image record still agrees with the tree |
| `tests/test_package_paths.py` | unit | `PLACEMENT_MANIFEST_PATH` anchors in the repository |
| `tests/conftest.py` | unit | `require_placement` |
| `tests/test_placement_manifest.py` | unit | the manifest's pins, digests, members and the detector's equality |
| `tests/test_pose.py` | unit | the detector's and the estimator's reading, the open, one real-model check |
| `tests/test_sam2.py` | unit | the preparation, the prompts, the open, one real-model check |
| `tests/test_proposal.py` | unit | the geometry on synthetic masks |
| `tests/test_propose.py` | unit | `propose` over the fakes, the wiring seam |
| `tests/test_ui_propose.py` | unit | the route, its guard, the invariant |
| `tests/fakes.py` | unit | `FakePoseFinder` and `FakeSegmenter` |
| `ui/src/pairs.test.ts` | unit | arrived, accepted, drag, forward |
| `ui/src/propose.test.ts` | unit | `due`, `asked`, `answered`, `refused`, `view` |
| `ui/src/composables/usePlacing.test.ts` | unit | the ask's state stays across steps |
| `ui/src/nokeys.test.ts` | unit | no command in the changed components |

No test is deleted or merged, so no table of removals is owed. Counts are read from the release's `tests-unit` metric, `scripts/metrics/tests_collected.py`.

## Dependencies

None.

## Risks / Trade-offs

- **The pins wait for a person.** Phase 2 needs the model host, which the run lacks, so the version halts there until the person has run the deriver and the fetch.
- **The segmenter's input and output names are expected, not read.** Phase 4's first task checks them against the unpacked files and halts the plan when they differ.
- **A proposal is a guess.** The prototype's overlap was 0.83 and 0.78; the operator reads every pair before forward, and forward waits for it.
- **DWPose may label the arm it does not need.** The bent case put a shoulder on the face; the nearest-arm rule keeps that arm out of the answer.
- **One ask takes seconds on the CPU.** It is a spinner, and the clicks still work.
- **Two commands fetch.** `provision fetch` lands a manifest's entries and `unpack fetch` lands them and unpacks; `PLACEMENT_REMEDY` and `make setup` name the second, and the first on the placement manifest leaves the members absent, which the next `unpack fetch` fills with no transfer.
- **The archive stays on disk.** It costs the operator its size, and saves a transfer for a gone member.
- **`make setup` fetches the models in every fresh worktree.** The files are large, as the tagger's are, and a worktree that has not run setup fails the checks that read them unless `ISEKAI_PLACEMENT=absent` says otherwise. Phase 2 is run in the build's own worktree for that reason.
- **0122 is not built at the cut.** Phases 5 and 6 begin with halt checks on its route, its photograph read and its editor files.

## Verdict

Ready to build. Each phase ends green; phase 2 is a person's, and nothing here spends money or needs a pod.
