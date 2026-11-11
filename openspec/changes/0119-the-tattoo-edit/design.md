# The tattoo edit — design

A tattoo placed by hand on a finished render is baked into it by an **edit**: `isekai ink` cuts the ink, `isekai edit tattoo-wai` requests the bake, `isekai render` runs it on the pod. Verdict: feasible, ready to build, in the phases of [tasks](tasks.md).

## Context

A flow is its manifest, graph and schema, and renders from a photograph. An edit takes a finished render and a hand-made **composite** (the render with the tattoo multiplied on) and writes a new image beside its source.

A prototype proved the mechanism on one case: a masked pass of WAI v17 under Differential Diffusion, held to the ink's lines by the union ControlNet in lineart mode, stitched back, the ink multiplied back at a weight.

```
photo ─ isekai ink ─▶ ink.png ─ Krita ─▶ composite.png
render.png + composite.png ─ isekai edit ─▶ outputs/NNN/<seed>.edit-<k>.{composite.png,json}   (pending)
isekai render <runs> ─ session ─ crop to the pod ─▶ sampled crop ─ stitch · lines (here) ─▶ <seed>.edit-<k>.png
```

The change touches the image's record (`config/models.json`, `isekai/boundary/provision.py`, `isekai/boundary/pod_start.py`), so it rebuilds the image once. The live proof of the edit is not here: it is the placement screen's last phase.

## Goals / Non-Goals

- **Goals:** the edit registry and its pin; `isekai ink`; `isekai edit` and its records; pending edits run by `isekai render`, quoted; edit images out of the render listings; discard that takes edits; promax in the manifest and the rebuilt image; the decisions and the guide.
- **Non-Goals:** the app, the eye edit, the line-weight dial, automatic masks and placement, the split image, the live verdict of an edit.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | an edit is `edits/<id>/`, flat, `edit.json` and `graph.json`, loaded and pinned like a flow | a flow takes one photograph and gates on a sheet | an edit under `flows/`; a flow manifest with a second image |
| [D2](#d2) | `edit.json` declares every dial once, and the crop box is each tattoo's own | declaration, never computation | dials computed at the call |
| [D3](#d3) | `isekai ink` is `isekai/shared/ink.py` under `config/ink.json`: an outline means a photograph | the tattoo photograph never leaves the machine | extraction on the pod |
| [D4](#d4) | the request derives ink, mask, box and control in `isekai/shared/tattoo.py` and refuses what a Multiply composite cannot be | the division is defined on a Multiply composite over a lit pixel | a silent best effort |
| [D5](#d5) | `isekai edit` writes the composite and a pending record into the render's group | `Run.flows` reads every run-level directory as a flow | a run-level `edits/` |
| [D6](#d6) | sampling is `isekai/pipeline/edit.py`; the transport helpers move to `isekai/boundary/comfy/prompt.py` | a stage imports no stage | importing `isekai/pipeline/generate.py` |
| [D7](#d7) | a session runs pending edits as `edit --pending` lines, after its renders, quoted at `per_edit_s` | one pod-creating verb, one quote | a second verb that rents |
| [D8](#d8) | an edit image is no render: the listings and the evaluator skip it, `show` reads it | an edit is not a render | edits counted as renders |
| [D9](#d9) | deleting a render takes its edits and their chain; `isekai discard` takes an edit path | an edit left in the group keeps it and its approval alive | a refusal while edits exist |
| [D10](#d10) | promax enters the manifest; the `pod_start.py` debt cards are paid; the image is rebuilt once, then proved by a render | an edit's files are in the image's record | a second rebuild |
| [D11](#d11) | the decisions in force are edited where they live: D51 new; D50, D36, D29, D14 amended | the decisions page says what holds | prose only in `design.md` |
| [D12](#d12) | tests sit at the lowest layer; no end-to-end test | the standards' lowest-layer rule | a browser test for a verb |
| [D13](#d13) | the skin-highlight rim of a photograph's extraction is recorded, not fixed | seen on one case | a fix without a second case |

### D1

- `isekai/foundation/edit.py` holds `EDITS_DIR`, `load_edit`, `tracked_edits` and `edit_digest`, stdlib only, modelled on `isekai/foundation/flow.py`.
- An edit's manifest is `edit.json`, in the first version of its own format, every key required, an unknown key refused naming the keys it reads.
- The digest covers every regular file of the directory, as `manifest_digest` does.
- `tests/test_flow.py` holds each tracked edit against an `EDIT_PINNED` entry and each digest against a `CHANGELOG.md` entry; a flow's `PINNED` is untouched.

### D2

`edit.json` keys: `edit`, `manifest_version`, `prompt`, `dials`, `nodes`, `checkpoint`, `controlnet`, `union_type`. `prompt` holds `positive`, `masterpiece, best quality, tattoo, ink tattoo, lineart, anime screencap`, and `negative`, the flows' own. `checkpoint` is the WAI v17 file; `controlnet` is promax at `union-promax/diffusion_pytorch_model_promax.safetensors`; `union_type` is the lineart label `canny/lineart/anime_lineart/mlsd`. A test holds them equal to what `graph.json` names.

| dial | value | read by |
|---|---|---|
| `denoise`, `strength`, `lines` | 0.2, 1.0, 0.4 | the sampler, the ControlNet, the lines multiply; the ones an override may change |
| `start_percent`, `end_percent` | 0.0, 1.0 | the ControlNet apply node |
| `long_side`, `margin` | 1216, 48 | the crop's sampling size and its margin in pixels |
| `min_aspect`, `max_upscale` | 0.5, 4 | the box guards |
| `grow`, `feather`, `ink_threshold` | 6, 4, 0.03 | the mask |
| `control_gain` | 1.6 | the control image's contrast, from the prototype's `b.py` |
| `lit_floor`, `rounding` | 8, 1 | levels out of 255: at most `lit_floor` reads no ink; above `rounding` lighter is refused |
| `steps`, `cfg`, `sampler_name`, `scheduler`, `clip_skip` | 28, 5, `euler_ancestral`, `normal`, -2 | the sampler and the clip-skip node |

`nodes` maps each role to its id in `graph.json`: `checkpoint`, `clip_skip`, `positive`, `negative`, `image`, `mask`, `control`, `controlnet`, `union`, `apply`, `sampler`. `graph.json` is the prototype's graph: checkpoint, clip skip, the prompts, the crop, the mask and the control loaded, the union ControlNet set to lineart and applied, Differential Diffusion on the model, the crop encoded under the mask, the sampler, decode and save.

### D3

- `isekai/shared/ink.py` holds `extract_ink(image, outline, neutral, depth)` and reads `config/ink.json`: `reach`, `white`, `floor`, `photo_depth`, `image_depth`, `depth_min`, `depth_max`, at the prototype's values (64, 80, 0.04, 1.6, 1.0, 1.0, 2.0).
- The mechanics are `extract.py` of the prototype: the skin under the ink is a max filter lifted and blurred, the layer is the photograph divided by it, bare skin scaled to white, the rest stretched by `floor`.
- An outline keeps the ink inside it only and is the layer's alpha, with neutral on and `photo_depth`; no outline keeps the whole image with neutral off and `image_depth`; each flag overrides its default.
- **Neutral** sets every channel to the layer's luminance. **Depth** raises the layer's Multiply factor to the power, so that a fill darkens; the brief's "on the ink's alpha" is read this way, because a power on an alpha would lighten it.
- Pillow and numpy are imported inside the functions.

### D4

`isekai/shared/tattoo.py` holds the maths of a request and of its stitch, each a function over arrays.

- **Ink** is the composite divided by the render, per channel, clipped to 1, and 1 wherever the render is at most `lit_floor`. **Darkness** is one minus the least channel of the ink.
- The **mask** is darkness above `ink_threshold`, grown by `grow` and feathered by `feather`. The **control** is darkness times `control_gain`, clipped, as white on black.
- Refusals, each naming its fix: a size that is not the render's; a composite carrying transparency or one that does not decode; no pixel darker than `ink_threshold`; a pixel lighter than the render by more than `rounding`.
- The **crop box** is the mask's box (mask above 8) plus `margin`, clipped to the image, widened to an aspect no thinner than `min_aspect`, then grown until the upscale to `long_side` is at most `max_upscale`; a box the image cannot grow to that refuses.
- The sampling size is the box scaled to `long_side` on its long side, each side a multiple of 8.

### D5

- `isekai edit <edit> <render> --composite <png>` takes `--denoise`, `--strength`, `--lines` and `--seed`. `<render>` is `<run>/<flow>/outputs/<NNN>/<seed>.png`, or `<seed>.edit-<k>.png` to chain: the next free `k` of that seed is the new one.
- It writes `<seed>.edit-<k>.composite.png`, the composite decoded and encoded again as RGB pixels with no profile or metadata, then `<seed>.edit-<k>.json`, kind `edit` (`EDIT_FILE`, `EditRecord`).
- The record holds `edit`, `edit_digest`, `source`, `source_sha256`, `composite_sha256`, `seed`, `dials` as they ran, `overridden`, and `crop` (box, size, `widened`, `grown`).
- The sampling seed is drawn from the wiring's `rng` as a render's is, and `--seed` repeats it. A request without its `<seed>.edit-<k>.png` is **pending**. The photograph a tattoo was cut from never enters a run.
- A second form, `edit --pending <run-id>/<flow>…`, runs pending requests on the wiring's client, as `generate` renders with `--server` and only assembles without.

### D6

- `isekai/pipeline/edit.py` holds the request, the pending listing and `sample`. `sample` re-derives the crops, uploads them, patches `graph.json` from `edit.json` and the record, submits it, then stitches and multiplies the ink back here.
- The stitch scales the sampled crop to the box, pastes it, blends it by the mask over the composite, then multiplies by one minus `lines` times the ink's darkness.
- The record is rewritten first, adding `graph_sha256`, `runtime` and `duration`; the image is written last, atomically, so a crash leaves a pending record.
- A failed sampling records no failure: the request stays pending and the refusal names the discard.
- `submit_and_wait` and `read_runtime`, with their helpers, move from `isekai/pipeline/generate.py` to `isekai/boundary/comfy/prompt.py`, exported by the package's front door; `graph_digest` moves to `isekai/foundation/flow.py`.

### D7

- `isekai render` with no request lists each named collection's pending edits as cells, less each `--without <runs>/<run-id>/<flow>`, and runs them in its pod after its renders; a request names renders alone and runs no edit.
- Free work first: every cell is derived and checked through `edit --pending` with no client, so a source that changed since the request refuses before anything is rented. A session may hold edits alone.
- `config/render.json` gains `per_edit_s`, 30; an edit takes `max(median of the newest recorded edit durations, per_edit_s)`, and `estimated` adds them, so the quote and the session still agree.
- The session's record and progress lines stay a render's; an edit's own record says what it did.

### D8

`rendered_seeds` and `is_render` already skip `<seed>.edit-<k>.png`, because its stem is no seed. A test holds it for the listings, a cell's newest and the evaluator's runs. `isekai show` reads an edit's files in a group instead of listing them as unread.

### D9

- `isekai/foundation/run.py` names an edit's files and parses an edit image's path.
- `discard_render` deletes every edit of the seed (images, records and composites) before it tests the group, so the group and its approval go as D50 says.
- `isekai discard <edit image>` deletes that edit and every edit whose source chain reaches it, through the edit stage. Both refuse while a render session holds the collection.
- `0111·R6` is paid in the same phase: the refusal test asserts the render's `7.render.json` stays.

### D10

- `config/models.json` gains the promax entry through `tools/derive_manifest.py`, its revision and SHA-256 read from the publisher at the phase and not before.
- `SELF_FETCHING_MODELS` classifies the node classes of `edits/tattoo-wai/graph.json`. The debt cards on `pod_start.py` are one-line edits: the `shm_type` docstring, `statvfs(pod.memory)`, the ceiling comment.
- The record in `config/image.json` is re-derived, the branch pushed, `build-image.yml` dispatched as `v0.79-rc1`, and the tag and digest re-recorded in `config/image.json` and `gpunit.toml`.
- The next phase proves the image by boot lines and one ordinary render, no edit. Both phases are a person's: the run has no network.

### D11

- `docs/decisions.md` gets D51, an edit is one flat directory pinned by its digest, named `<what>-<base>`, its image written beside its source.
- D50 says a render's deletion takes its edits; D36 says a session renders and edits; D29 gains the line that a tattoo is added by an edit after the flow; D14 says an edit is not a flow.
- `docs/data-flow.md` scopes *img2img is a closed avenue*: an edit encodes a render, never the photograph, so composition still comes from noise.
- `docs/edit-tattoo.md` is the Krita-first guide, with `isekai ink` its first step.

### D12

See [Tests](#tests). Every new test carries its `spec` marker.

### D13

The extraction of a photograph carries the skin's highlight rim into the layer; it is seen on one case. The cut writes no card: the rim is recorded as a debt card when the build or the release writes its own, and fixed when a second case shows its shape.

### D14

No pod proof in this change. The person waived D28's metered pod proof of `v0.79-rc1` on 2026-11-11: the image is
built and re-pinned (phase 5), and the operator's own test of the tattoo screens, after the placement versions, is
its first run on a pod. D28 itself is unchanged and may be revisited.

## Tests

Tests sit at the lowest layer that can fail: arrays for the maths, the stage over `FakeComfyClient` for the sampling, `dispatch` for the verbs. No test boots a pod or a browser, and the end-to-end suite gains none: `git diff --name-only main -- tests/e2e` prints nothing at the release.

| file | layer | holds |
|---|---|---|
| `tests/test_flow.py` | unit | the edit's load, refusals, `EDIT_PINNED`, and its digest in the changelog |
| `tests/test_package_paths.py` | unit | `EDITS_DIR` resolves inside the repository |
| `tests/test_ink.py` | unit | the extraction, the outline, neutral, depth, the verb |
| `tests/test_edit.py` | unit | derivation, the refusals, the crop guards, the records, the chain, the sampling over the fake client |
| `tests/test_edit_session.py` | unit | the session's lines, the quote, `--without`, the listings, discard |
| `tests/test_generate.py`, `tests/test_artifact_bytes.py`, `tests/stages.py` | unit | the moved helpers, imported from their new places |
| `tests/test_render.py` | unit | `per_edit_s` and the estimate |
| `tests/test_pipeline_cli.py` | unit | the `0111·R6` assert |
| `tests/test_run_view.py` | unit | `show` reads an edit's files |
| `tests/test_manifest_binding.py`, `tests/test_pod_start.py` | unit | the edit's graph is classified and its files declared; the memory check reads the memory directory |

No test is deleted or merged, so no table of removals is owed. Counts are read from the release's `tests-unit` metric, `scripts/metrics/tests_collected.py`.

## Dependencies

None.

## Risks / Trade-offs

- **The quality of a bake is not proved here.** The live verdict is the placement screen's last phase, on this image; a bad crop surfaces there.
- **A failed sampling is retried by the next session.** Nothing records it, so a graph the endpoint rejects costs each session a try; the operator discards the edit.
- **The promax digest is read at its phase.** The plan holds no value for it: the cut had no network.
- **The rebuild's phases are a person's.** The run halts at the first and rejoins after the second.
- **`edits/` is read by no listing of flows.** A flow-wide check that walks `flows/` does not see it; the checks of an edit are its own.
- **The brief's Decisions table holds the cut's own choices.** The near-black floor, the control gain and the reading of depth are the cut's, in the rows it added.

## Verdict

Feasible. Each phase ends green, the rebuild's phases on a person, and the edit's live verdict waits for the placement screen.
