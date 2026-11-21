---
bump: patch
version: 0.88.4
after: [0193-the-command-builder]
---

# The ONNX opener

An ONNX session is made by one function, `cpu_session` in `isekai/boundary/onnx.py`, which also holds the telemetry switch; `wd14`, `pose`, `sam2` and the evaluator's `face` call it, and every printed byte stays equal.

Reading map: [design](design.md) holds the opener, each site before and after, and its cases, [tasks](tasks.md) its phases: the opener, the callers, the documents.

## Why

A session is made in `wd14`, `pose`, `sam2` and the evaluator's `face`, each spelling the provider list, and `wd14` holds the telemetry switch the others import. A new module would copy the spelling, and only a scan of the sources fails on a copy that forgets the switch.

The next boundary version, *the manifest table*, edits the same modules. It is a smaller edit once the session is made in one place.

## What Changes

- `isekai/boundary/onnx.py` is new and imports only the standard library: `silence_onnxruntime()`, the telemetry switch moved from `wd14.py`, and `cpu_session(runtime, model, options=None)`, the one maker of a session on the CPU provider alone.
- `OnnxSession` of `wd14.py`, `OnnxPoseFinder` of `pose.py`, `OnnxSegmenter` of `sam2.py` and `_session` of `evaluation/face.py` call `cpu_session` in place of `InferenceSession`.
- Each module keeps its own import of `onnxruntime` and its own text for an absent wheel, and still sets the switch before it imports.
- `wd14.py` binds `silence_onnxruntime` back from `onnx.py`; `pose.py`, `sam2.py` and `face.py` import it from `onnx.py`.
- Cases for the opener are written before it; a mutation run over the lines of each site that made a session passes before the switch and over the opener after.
- The boundary README gains the row and the derived table of `onnx.py`; `docs/modules.md` names it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Behaviour is unchanged, and the change carries `skip_specs`.

## Impact

- `isekai/boundary/onnx.py`, `isekai/boundary/wd14.py`, `isekai/boundary/pose.py`, `isekai/boundary/sam2.py` and `evaluation/face.py`.
- `tests/test_wd14.py` for the opener's cases, and for a survivor of the mutation run the test file of its site; no existing test's assertion changes, and no ratchet row goes.
- `isekai/boundary/README.md` and `docs/modules.md`; `tests/mutants.json` only for a find an edit moves.
- The import graph `python -m isekai` loads gains `onnx.py`, which imports nothing of `isekai` and no wheel.
- No decision is added, and no image-frozen file changes.

## Not in this change

- One text for an absent wheel: each module keeps its own, and tests pin what each prints.
- The import of `onnxruntime`: each module keeps its seam, `_require` of `wd14.py`, `_import` of `face.py` and the `runtime` parameter of `open_pose` and `open_segmenter`.
- The image maths of `pose.py` and `sam2.py`.
- The manifest table, a refusal for a damaged vocabulary, and any change to an image-frozen file: *the manifest table* and *the split image* hold them.
- Any ratchet row, any printed text, and any file under `ui/` or `tools/`.
