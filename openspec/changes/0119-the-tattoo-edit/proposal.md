---
bump: minor
debt: [0060·R5, 0060·R6, op·pod-start-comment, 0111·R6]
---

# The tattoo edit

A tattoo placed by hand on a finished render is baked into it on the pod: `isekai ink` extracts it, `isekai edit tattoo-wai` requests it, `isekai render` bakes it.

Reading map: [design](design.md) holds the registry, the maths, the records, the session and the image's rebuild, [tasks](tasks.md) its phases.

## Why

The flows carry no tattoo, and a tattoo is local and arbitrary: it is added after the render, by hand, and a masked low-denoise pass makes the ink sit in the skin. A prototype proved the mechanism on one case. The edit is the first of a family, named for the family and built for one member.

The tattoo edit also pays the debt the image's record held back: its files are the image's, so opening them is a rebuild, and this change rebuilds the image once.

## What Changes

- An edit is one flat directory, `edits/tattoo-wai/`, with its manifest and graph, loaded and pinned by digest.
- New requirement, *An edit is one flat directory, pinned by its digest*.
- New requirement, *The ink is cut by `isekai ink`*: from a photograph inside an outline, neutral, depth 1.6; from a tattoo image, colour kept, depth 1.0.
- New requirement, *An edit request is made from a render and its composite*: the composite kept as pixels, a drawn seed, the dials as they ran, a chain.
- New requirement, *A request the composite cannot support is refused*: size, transparency, no ink, lighter.
- New requirement, *The crop is the tattoo's own*: its box widened and grown by guards.
- New requirement, *A render session runs every pending edit*: in the same pod, after its renders, derived before anything is rented.
- New requirement, *An edit's time is estimated from its work*: at `per_edit_s` or the recorded median.
- New requirement, *An edit image is no render*: out of every render listing, read by `show`.
- New requirement, *A discard takes edits*: a render's edits go with it, and an edit's chain goes with the edit.
- New requirement, *Every file an edit's graph names has a manifest entry*: promax is declared.
- Modified requirement, *The discard verb deletes a render named by its image path*: an edit image's path is accepted.
- `isekai render` and the quote count pending edits; the transport helpers move to `isekai/boundary/comfy/prompt.py`.
- The image is rebuilt as `v0.79-rc1` with promax, the debt cards on `pod_start.py` and the re-derived record, and proved by boot and an ordinary render.
- The decisions D51 (new), D50, D36, D29 and D14 are edited where they live, and `docs/edit-tattoo.md` is the guide.

## Capabilities

### New Capabilities

- `edit`: the edit registry, the ink, the request, the session's pending edits, their time, their listing, their discard and their models.

### Modified Capabilities

- `cli`: the discard verb accepts an edit image's path.

## Impact

- New: `edits/tattoo-wai/edit.json`, `edits/tattoo-wai/graph.json`, `isekai/foundation/edit.py`, `config/ink.json`, `isekai/shared/ink.py`, `isekai/shared/tattoo.py`, `isekai/pipeline/edit.py`, `isekai/boundary/comfy/prompt.py`, `tests/test_ink.py`, `tests/test_edit.py`, `tests/test_edit_session.py`, `docs/edit-tattoo.md`.
- Changed: `isekai/foundation/artifacts.py`, `isekai/foundation/run.py`, `isekai/foundation/flow.py`, `isekai/boundary/comfy/__init__.py`, `isekai/pipeline/generate.py`, `isekai/interface/cli.py`, `isekai/interface/render.py`, `isekai/interface/run_view.py`, `config/render.json`.
- The image: `tools/derive_manifest.py`, `config/models.json`, `isekai/boundary/provision.py`, `isekai/boundary/pod_start.py`, `config/image.json`, `gpunit.toml`.
- The record: `CHANGELOG.md`, which each pinned digest and the proof's lines enter.
- Tests: `tests/test_flow.py`, `tests/test_package_paths.py`, `tests/test_generate.py`, `tests/test_artifact_bytes.py`, `tests/stages.py`, `tests/test_render.py`, `tests/test_pipeline_cli.py`, `tests/test_run_view.py`, `tests/test_manifest_binding.py`, `tests/test_pod_start.py`.
- Docs: `docs/decisions.md`, `docs/data-flow.md`, `docs/modules.md`, `README.md`, `isekai/shared/README.md`, `isekai/pipeline/README.md`, `isekai/boundary/README.md`.

## Not in this change

- The app: the tool on the large view, the upload, the quote, the `?`.
- The eye edit and the line-weight dial.
- An automatic mask, automatic placement and the click chain.
- The split image.
- The edit's live verdict, CLI and UI: the placement screen's last phase.
- An automatic Levels on the extraction.
- Placement inside isekai: Krita stays the operator's tool.
