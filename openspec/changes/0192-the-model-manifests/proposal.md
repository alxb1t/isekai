---
bump: patch
after: [0191-the-wiring-resolvers]
---

# The model manifests

A model opener takes its manifest's path, `unpack.main` takes its fetcher, and `unpack` leaves the patch ratchet.

Reading map: [design](design.md) holds the keywords and the tests' arrangements, [tasks](tasks.md) its phases.

## Why

`PATCHED_MODULES` of `tests/test_ratchets.py` lists `isekai.boundary.unpack`, and tests patch the manifest a model opener reads: `unpack.PLACEMENT_MANIFEST_PATH` for the pose finder and the segmenter, and `provision.load_manifest` and `provision.VOCABULARY_MANIFEST_PATH` for the tagger and the vocabulary. A patch of a module's name is global state that strands silently when the reading code moves. The manifest is a path a test already holds, so it is a parameter.

The row of `unpack` empties only when its last patch goes: the manifest paths and the fetcher `unpack.main` builds. The rows that stay — `provision`'s import-time tripwires and its recording spy, and the others — are named in the principles' *Known breaks* with their reasons.

## What Changes

- `isekai/boundary/wd14.py`: `verified_paths` and `open_session` take `manifest=`, a path.
- `isekai/interface/wiring.py`: `load_vocabulary` takes `manifest=`, a path.
- `isekai/boundary/pose.py`: `verified_paths` and `open_pose` take `manifest=`, a path defaulting to the placement manifest.
- `isekai/boundary/sam2.py`: `open_segmenter` takes `manifest=`, a path defaulting to the placement manifest.
- `isekai/boundary/unpack.py`: `main` takes `fetcher=`, a factory defaulting to `HuggingFaceFetcher`.
- Each test that patched a manifest or the fetcher passes it instead; no assertion changes. One case holds the default fetcher.
- The row `isekai.boundary.unpack` leaves `PATCHED_MODULES`, and `PATCHED_ROWS` is 17.
- The standing mutants `BD-1` and `BD-10b` are re-pointed to the edited lines.
- The *Known breaks* of *A component is a contract* names each module `PATCHED_MODULES` still lists, with its reason.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change carries `skip_specs: true`: no requirement's text changes and none is added.

## Impact

- Code: `isekai/boundary/wd14.py`, `isekai/boundary/pose.py`, `isekai/boundary/sam2.py`, `isekai/boundary/unpack.py`, `isekai/interface/wiring.py`.
- Tests: `tests/test_wd14.py`, `tests/test_wd14_runtime.py`, `tests/test_vocabulary_manifest.py`, `tests/test_pose.py`, `tests/test_sam2.py`, `tests/test_provision_unpack.py`, `tests/test_ratchets.py`, `tests/mutants.json`.
- Docs: `docs/principles.md`, and the changelog entry the build writes. No decision is added or amended.
- No format version moves, no printed text changes, no flow is re-pinned.

## Not in this change

- `isekai/boundary/provision.py`: the pod image copies it; its row and its tripwires stay.
- Any file under `ui/`, `tools/` or `evaluation/`.
- A refusal for a damaged vocabulary, and the manifest table: they wait for a version planned after this one merges.
- The ONNX session opener shared by the tagger, the pose finder and the segmenter.
