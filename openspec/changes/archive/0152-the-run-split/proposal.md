---
bump: patch
version: 0.87.8
after: [0151-the-hub-rules]
---

# The run split

`isekai/foundation/run.py` splits into the siblings `names.py`, `rundir.py`, `layout.py` and `failures.py`, and stays the front that re-exports every name, with behaviour unchanged.

Reading map: [design](design.md) holds where each name goes, the import graph and how the move is proved, [tasks](tasks.md) holds the phases: names and rundir, layout, failures, the documents.

## Why

`run.py` holds the run directory's identity, its layout, its numbering, its failure budgets and its command text in one file. It is a listed row of the ratchet ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)), and each version that adds a layout name or a budget grows it. Its clusters have no cycle between them, but reads cross them, `rendered_at` into `stage_command` and `photo_of` into `migrate_command`, so those clusters stay in the front.

## What Changes

- `isekai/foundation/names.py` is new. It holds the identity of a run (the id's constants, `slug`, `digest_of`, `run_id`, `media_type`) and the layout's names and patterns, `FRAME_NAME` with them.
- `isekai/foundation/rundir.py` is new. It holds `Run`, the frame's photograph fields and `assign`.
- `isekai/foundation/layout.py` is new. It holds numbering, the seeds apart from `rendered_at`, and the edit files.
- `isekai/foundation/failures.py` is new. It holds `Kind`, `BUDGETS`, `Attempt` through `check_budget`, `across` and `StageFailure`.
- `run.py` keeps the roots, `open_run` and `find_run`, `rendered_at`, the command text with `refusal_for`, the migration state and the provenance records. It imports the siblings and re-exports every name under `__all__`, so no importer changes.
- The UI's artifact tripwire lists `artifact_name` under `isekai.foundation.layout` too, and a twin holds the new row.
- `run.py`'s ratchet row goes, in the phase where the file falls under the ceiling. A new decision says the siblings are imported through `run.py`.
- `tests/mutants.json` points the entries FN-1, FN-2, FN-4a, FN-4b and FN-6 at their new homes, their text unchanged.
- The foundation README, `docs/modules.md`, `docs/data-flow.md`, D21 and the docstring of `run.py` say where the moved names live.

No requirement changes: no path, filename, record, refusal or command text changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change declares `skip_specs: true`.

## Impact

- Code: `isekai/foundation/run.py` loses the moved lines; the new modules hold them. No importer changes.
- Tests: `tests/test_ratchets.py` loses a row, `tests/test_ui.py` gains a tripwire row and a twin, `tests/mutants.json` points the moved entries at new paths, and `tests/test_run_directory.py` gains a test only where one kills a survivor.
- Documents: `docs/decisions.md`, `docs/modules.md`, `docs/data-flow.md`, `isekai/foundation/README.md`, the *Imported by* table the deriver writes.
- No test's assertion, nothing under `tests/record/`, no format version, no re-pin and no image-frozen file changes.

## Not in this change

- Any importer: each keeps reading its names from `isekai.foundation.run`.
- The `RUNS_ROOT` patch and the roots: they stay in `run.py`, where the test patches them.
- `refusal_for`'s positional parameters: its row stays listed, until a version rewrites the function.
- The library's and the session's names: when the server's seams have moved the patched names the library's code reads.
- The runs' predicate and the loaders' shared lines: with the base's own versions.
- The refusal at the last number an artifact's name can spell: a patch of its own, cut after this one releases.
